# Dynamic Tool Agent (Zero-Knowledge LangGraph)

Bu proje, **LangGraph** tabanlı, tamamen modüler ve dinamik bir **Zero-Knowledge** araç kullanım (tool-use) ajanıdır. Ajan, başlangıçta (System Prompt içerisinde) hiçbir aracın adını veya yeteneğini (schema) bilmez. Gelen kullanıcı isteklerini analiz eder, gerekli olan araçları **vektör veritabanında (ChromaDB)** semantik arama yaparak bulur ve sadece ihtiyaç duyulan aracın şemasını o an (runtime) LLM'e enjekte eder.

Bu mimari, yüzlerce hatta binlerce aracı aynı anda desteklemek isteyen ve prompt limitlerini/kirliliğini önlemek isteyen gelişmiş sistemler için tasarlanmıştır.

## 🌟 Temel Mimari ve İlham Alınan Makaleler

Bu proje, akademik literatürdeki en son yaklaşımları pratik bir **RAG (Retrieval-Augmented Generation) + Agent** hibritinde birleştirir:

1. **ToolReAGt (Decomposition)**: Kullanıcının karmaşık görevleri tek seferde çözülmeye çalışılmaz. Ajan, görevi alt adımlara (sub-tasks) böler ve her bir adım için ayrı bir semantik arama sorgusu üretir.
2. **AutoTools (Schema-in-Runtime)**: LLM, sistem komutunda statik olarak tanımlanmış araç listesine bağımlı değildir. Her adımda "Sen bir araç seçicisin" vb. promptlar kullanmadan, sadece seçilen aracın Pydantic şeması bağlama eklenir. LLM parametreleri doldurup döner.
3. **TIG (Tool Inertia Graph)**: Araçların başarılı kullanımı kayıt altına alınır (`logs/executions.jsonl` ve `logs/tool_stats.json`). Hiç kullanılmamış araçlara 1.0 (nötr) katsayısı verilirken, başarıyla kullanılan araçların "atalet" (inertia) katsayısı güncellenir. Bu sayede semantik aramada sürekli aynı araçların ağırlıklandırılmasının / dışlanmasının önüne geçilir ve kullanım geçmişi (history) tavsiye sistemine matematiksel olarak entegre edilir.

---

## 🛠 Proje Yapısı

```bash
dynamic-tool-agent/
├── agent/
│   ├── main_agent.py        # LangGraph StateGraph ve ana düğümlerin (nodes) tanımı
│   └── __init__.py          # Dışarıya açılan arabirim (agent.invoke)
├── logs/
│   ├── execution_logger.py  # Pydantic ve Rich ile JSONL + Konsol loglama yöneticisi
│   └── executions.jsonl     # Ajanın yaptığı her bir tool çağrısının trace verisi
├── registry/
│   ├── models.py            # ToolSchema, ToolParameter vb. Pydantic tanımları
│   ├── tool_registry.py     # Araçların memory'de tutulduğu ve yönetildiği sınıf
│   └── tools/               # Tüm araçların (weather_service, translation vs.) bulunduğu klasör
├── search/
│   ├── embedder.py          # Sentence-Transformers ile semantik embedding üretimi
│   ├── tool_manager.py      # ChromaDB + TIG Atalet + Tag Eşleşmesi ile araç arama
│   └── vector_store.py      # ChromaDB VectorStore sarmalayıcısı
├── tests/
│   └── test_agent.py        # Uçtan uca pytest entegrasyon testleri
└── pyproject.toml           # Bağımlılıklar ve proje meta verileri
```

---

## 🚀 Kurulum

### 1. Ortam ve Bağımlılıkların Yüklenmesi
Bu proje `uv` (veya `pip`) paket yöneticisini kullanır. `uv` kullanarak veya sanal ortam oluşturarak bağımlılıkları yükleyin:

```bash
uv pip install -e .
# VEYA klasik pip ile:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt # (veya pyproject.toml bağımlılıkları)
```

**Temel Kütüphaneler:**
- `langgraph`, `langchain-core`, `langchain-groq`
- `chromadb`, `sentence-transformers`
- `pydantic`, `rich`

### 2. Çevresel Değişkenler (`.env`)
Proje ana dizininde bir `.env` dosyası oluşturun ve **Groq API Key**'inizi ekleyin:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Semantik arama barajı. ChromaDB L2 distans skorlamasında 
# bu değeri aşan araçlar LangGraph ağına dahil edilir.
CONFIDENCE_THRESHOLD=0.20
CHROMA_PERSIST_DIR=./chroma_db
```

---

## ⚙️ Nasıl Çalışır? (Graph Akışı)

LangGraph üzerinde tanımlı akış şu şekildedir:

1. **`analyze_task`**: Kullanıcı girdisi alınır. LLM, görevi gerçekleştirmek için gereken alt adımları (sub-tasks) ve her adım için 1 cümlelik arama sorgusunu JSON formatında böler.
2. **`search_tools`**: Güncel adımın arama sorgusu alınarak `ToolManager` üzerinden aranır. 
   - *Arama formülü*: `Combined Score = (1.0 - (L2_Distance / 2.0)) * Inertial_Score * Keyword_Boost`
3. **`check_tools` (Conditional)**: Araç bulunursa işleme devam edilir, bulunamazsa hata akışına sapılır.
4. **`select_and_prepare`**: Bulunan 1. sıradaki aracın şeması (Pydantic statik JSON'ı) LLM'e verilir. LLM sadece parametreleri üretir.
5. **`execute_tool`**: İlgili araç çalıştırılır, latency hesaplanır, logs dizinine JSONL olarak trace yazılır.
6. **`step_check` (Conditional)**: Eğer sıradaki başka bir alt adım (ToolReAGt döngüsü) varsa başa sarılır, bittiyse yanıt sentezine geçilir.
7. **`format_response`**: Tüm adım sonuçları birleştirilerek kullanıcıya doğal dilde tek bir cevap olarak iletilir.

---

## 📝 Loglama ve İzleme

Sistem `logs/execution_logger.py` aracılığıyla her işlemi mükemmel bir şekilde izler:

- **Terminal (Rich)**: Süreç anlık olarak terminalinize şık bir arayüzle yansır (Latency, Başarı durumu, Hata mesajları).
- **Kalıcı Loglar (`executions.jsonl`)**: Her işlem `trace_id` ile eşsiz bir json objesi olarak kaydedilir. Bu sayede ajanın geçmişteki hareketlerini ve "latency" dağılımlarını veri analitiğiyle inceleyebilirsiniz.

Örnek Log:
```json
{
  "trace_id": "a1d3060e-b58f-481d-a513-5143acc7e129",
  "timestamp": "2026-03-24T17:16:40.25Z",
  "user_input": "İstanbul'da bugün hava nasıl?",
  "found_tool_names": ["weather_service"],
  "selected_tool": "weather_service",
  "success": true,
  "latency_ms": 55.6
}
```

---

## 🔧 Yeni Bir Araç (Tool) Eklemek

Yeni bir araç eklemek tamamen "tak-çalıştır" mantığındadır ve prompt değişikliği gerektirmez.

1. `registry/tools/` klasörüne `yeni_aracim.py` dosyası açın.
2. İçerisinde `SCHEMA` isimli bir `ToolSchema` nesnesi tanımlayın (Bkz. `document_reader.py`). `tags` listesini hedef kelimelerle doldurmaya özen gösterin.
3. İçerisinde bir `def execute(params: dict) -> dict:` fonksiyonu kodlayın.
4. `registry/tools/__init__.py` dosyasına girerek `TOOL_LIST` ve `TOOL_EXECUTORS` listelerine yeni aracınızı (ve schema'yı) ekleyin.

Agent bir sonraki çalışışında (başlatıldığında) `VectorStore`'a bu aracın şemasını otomatik olarak vektörize edip indeksleyecektir. Sistem anında bu aracı "bulabilir" hale gelecektir. Artık LLM de dahil olmak üzere başka hiçbir yere kodu tanıtmanız gerekmez.

---

## 🧪 Testleri Çalıştırma

Projenin entegrasyonlarını ve çoklu adım başarısını ölçmek için uçtan-uca (end-to-end) test script'i bulunmaktadır. Test çalıştırırken `.env` dosyanızda API key'inizin tanımlı olduğundan emin olun.

```bash
# Python modülü olarak testleri çalıştırma
python tests/test_agent.py

# Alternatif olarak pytest kuruluysa:
pytest tests/test_agent.py -v -s
```

Test dosyası şu özellikleri kontrol eder:
- Tek adımlı bir arama (Hava Durumu)
- Tek adımlı bir veri sorgulama (Döviz Çevirici)
- Belge / İnternet üzerinden makale özetleme
- Multi-step (Çeviri + Hava durumu) ToolReAGt decomposition kontrolü
- Geçersiz aramalarda sistemin "uygun araç bulunamadı" yanıtını doğru şekilde `format_response` ile verebilmesi.
