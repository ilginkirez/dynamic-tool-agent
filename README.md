# Tool Agent (Zero-Knowledge LangGraph)

Bu proje, **LangGraph** tabanlı, tamamen modüler ve dinamik bir **Zero-Knowledge** araç kullanım ajanıdır. Ajan, başlangıçta  hiçbir aracın adını veya yeteneğini bilmez. Gelen kullanıcı isteklerini analiz eder, gerekli olan araçları **vektör veritabanında (ChromaDB)** semantik arama yaparak bulur ve sadece ihtiyaç duyulan aracın şemasını o an  LLM'e enjekte eder.

Bu mimari, yüzlerce aracı aynı anda desteklemek isteyen ve prompt limitlerini önlemek isteyen gelişmiş sistemler için tasarlanmıştır.

## 🌟 Temel Mimari ve İlham Alınan Makaleler

Bu proje, akademik literatürdeki en son yaklaşımları hibrit bir şekilde birleştirir:

1. **3.1 ToolReAGt — Iterative Sub-task Decomposition**
   *(Braunschweiler et al. ACL 2025 — "Tool Retrieval for LLM-based Complex Task Solution via Retrieval Augmented Generation")*
   
   Bu çalışma, 2000+ tool içeren UltraTool benchmark'ında klasik RAG yaklaşımına göre %8.9 daha iyi recall skoru elde etmiştir. Temel katkısı, görevi tek bir sorgu olarak değil, alt görevlere bölerek her biri için ayrı retrieval yapmasıdır.
   
   **Sistemdeki Karşılığı:**
   - `analyze_task` node'u görevi JSON formatında alt görevlere böler.
   - Her alt görev için bağımsız `search_query` üretilir.
   - LangGraph döngüsü her alt görevi sırayla işler.

2. **3.2 AutoTools — Callable Function Template**
   *(ACM WWW 2025 — "AutoTools: Tool Calling Integration for Open-Source LLMs")*
   
   LLM'in tool dokümantasyonunu okuyarak aracı otomatik olarak callable Python fonksiyonuna dönüştürdüğü bu yaklaşım, manuel şablon ve özel token kullanımını ortadan kaldırır. Büyük tool setlerinde ölçeklenebilirlik sağlar çünkü her yeni tool için sistem kodu değişmez.
   
   **Sistemdeki Karşılığı:**
   - `ToolSchema` modeline `callable_template` alanı eklendi.
   - `select_and_prepare` node'u bu template'i LLM'e vererek parametre doldurur.
   - LLM serbest format üretmek yerine önceden tanımlı şablonu doldurur → halüsinasyon riski düşer.

3. **3.3 TIG — Tool Inertia Graph**
   *(AAAI 2025 — Tool Inertia Graph tabanlı akıllı tool seçimi)*
   
   TIG, geçmiş kullanım verilerini bir graph yapısında tutarak sık kullanılan tool'lar için LLM çağrısını atlayan bir mekanizma önerir. Yüksek güven skoru olan tool'lar doğrudan çalıştırılır; düşük güvenlikli durumlar LLM'e havale edilir.
   
   **Sistemdeki Karşılığı:**
   - Execution logger her tool çağrısını `trace_id`, `latency`, `success/fail` ile JSONL formatında kaydeder.
   - Toplanan bu veri, production aşamasında tam TIG implementasyonunun eğitim verisi olarak tasarlanmıştır.
   - Prototipte graph yapısı yerine usage-based logging olarak sadeleştirilmiştir.
   
   > *Şu an sistemde tam anlamıyla bir TIG implementasyonu bulunmuyor. Ancak altyapısı hazırlanmış durumda ve execution logger üzerinden toplanan verilerle bu yapının ileride kurulması hedefleniyor.*

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

### 3. Uygulamayı Çalıştırma (İnteraktif Terminal)
Sistemi asistan modunda başlatmak ve doğrudan sohbet/görev vermek için ana dosyayı çalıştırın:

```bash
python main.py
```
Ajan yüklendikten sonra `🧑 Sen:` komut satırına dilediğiniz (çok adımlı, doğal dilde) isteği yazıp ajan hareketlerini izleyebilirsiniz. Çıkmak için `q` veya `exit` yazmanız yeterlidir.

---

## ⚙️ Nasıl Çalışır? (Graph Akışı)

LangGraph üzerinde tanımlı akış şu şekildedir:

1. **`analyze_task`**: Kullanıcı girdisi alınır. LLM, görevi gerçekleştirmek için gereken alt adımları ve her adım için 1 cümlelik arama sorgusunu JSON formatında böler.
2. **`search_tools`**: Güncel adımın arama sorgusu alınarak `ToolManager` üzerinden aranır. 
   - *Arama formülü*: `Combined Score = (1.0 - (L2_Distance / 2.0)) * Inertial_Score * Keyword_Boost`
3. **`check_tools` (Conditional)**: Araç bulunursa işleme devam edilir, bulunamazsa hata akışına sapılır.
4. **`select_and_prepare`**: Bulunan 1. sıradaki aracın şeması (Pydantic statik JSON'ı) LLM'e verilir. LLM sadece parametreleri üretir.
5. **`execute_tool`**: İlgili araç çalıştırılır, latency hesaplanır, logs dizinine JSONL olarak trace yazılır.
6. **`step_check` (Conditional)**: Eğer sıradaki başka bir alt adım (ToolReAGt döngüsü) varsa başa sarılır, bittiyse yanıt sentezine geçilir.
7. **`format_response`**: Tüm adım sonuçları birleştirilerek kullanıcıya doğal dilde tek bir cevap olarak iletilir.

---

## 📝 Loglama ve İzleme

Sistem `logs/execution_logger.py` aracılığıyla her işlemi izler:

- **Terminal**: Süreç anlık olarak terminalde gösterilir.
- **Kalıcı Loglar (`executions.jsonl`)**: Her işlem `trace_id` ile eşsiz bir json nesnesi olarak kaydedilir. Ajanın tüm yetenek kanıtları bu audit trail içinde toplanır.

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

Yeni bir araç eklemek basittir ve prompt değişikliği gerektirmez.

1. `registry/tools/` klasörüne `yeni_aracim.py` dosyası açın.
2. İçerisinde `SCHEMA` isimli bir `ToolSchema` nesnesi tanımlayın (Bkz. `document_reader.py`). `tags` listesini hedef kelimelerle doldurmaya özen gösterin.
3. İçerisinde bir `def execute(params: dict) -> dict:` fonksiyonu kodlayın.
4. `registry/tools/__init__.py` dosyasına girerek `TOOL_LIST` ve `TOOL_EXECUTORS` listelerine yeni aracınızı (ve schema'yı) ekleyin.

Agent bir sonraki başlatıldığında `VectorStore`'a bu aracın şemasını otomatik olarak vektörize edip indeksleyecektir. Sistem anında bu aracı bulabilir hale gelecektir. Artık LLM de dahil olmak üzere başka hiçbir yere kodu tanıtmanız gerekmez.

---

## 🧪 Testleri Çalıştırma

Projenin entegrasyonlarını ve çoklu adım başarısını ölçmek için uçtan-uca test script'i bulunmaktadır. Test çalıştırırken `.env` dosyanızda API key'inizin tanımlı olduğundan emin olun.

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

---

## 7. Gelecek Çalışmalar

Sistemi production seviyesine taşımak için öngörülen bazı geliştirmeler şunlardır:

- **Tam TIG Implementasyonu:** Toplanan log verilerinin gerçek bir graph yapısına dönüştürülmesi. Güven skoru yüksek araçlar LLM'e hiç gidilmeden doğrudan (sıfır gecikme ile) çalıştırılabilir.
- **ToolReAGt'in Tam iteratif Yapısı:**  İleride her sub-task kendi ReAct döngüsünü (araç bulunamazsa sorguyu baştan formüle etme) döndürecek şekilde evrilebilir.
- **Cross-Encoder Reranking:** Pahalı API çağrıları yerine, Sentence-Transformers tabanlı yerel bir `Cross-Encoder` (örn: *ms-marco*) ile arama sonuçları çok daha hızlı ve maliyetsiz bir şekilde sıralanabilir.
- **Gelişmiş Tool Versioning:** Meta veri olarak tutulan deprecation bilgisinin, aktif kullanıcı oturumlarını otomatik olarak "replaced_by" isimli yeni araca yönlendirmesi 

---

## 8. Sonuç

Bu çalışmada geliştirilen sistem, temel gereksinimleri eksiksiz karşılayan ve üç akademik çalışmadan ilham alan katmanlı bir mimari sunmuştur:

- **Zero-knowledge başlangıç prensibi:** Main Agent hiçbir tool tanımı bilmeden başlar, ihtiyaç anında dinamik olarak öğrenir.
- **Hibrit arama:** Keyword filtresi + semantik arama + LLM reranking üçlüsü false-positive riskini minimize eder.
- **Genişletilebilirlik:** Tool eklemek için tek bir Python dosyası oluşturmak yeterlidir; sistemin geri kalanında değişiklik gerekmez.
