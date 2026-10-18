# SlideReady hareket dili: yönetmen el kitabı

Bu dosya Yönetmen adımında okunur. Amaç, PowerPoint'in kendi efektleriyle elle yapılması çok zor, her slaytta
farklı ve bir motion-graphics stüdyosundan çıkmış gibi duran bir sonuç kurmaktır. SlideReady'nin işi **katmanlarla**:
PowerPoint her öğeyi ayrı katman olarak çizer; hareket bu öğelerin kendisine verilir. Hareketi süs olsun diye değil,
izleyicinin gözünü slaytın okuma sırasına taşımak için kurarsın.

## 1. Değişmezler (pazarlık yok)

1. İlk kare boştur: yalnızca slaytın arka planı. Boş açılış 0,3–0,6 sn sürer.
2. **Kamera sabittir.** Pan, zoom, kamera turu, geri çekilme, slaytın bütününe eğim ya da paralaks yok. Arka plan
   ilk kareden son kareye kımıldamaz. Hareket eden yalnızca öğelerdir.
3. **Her öğe kendi hareketiyle gelir.** Tablo satır satır ya da hücre hücre, kartlar tek tek, liste maddeleri
   madde madde, grafik seri seri, ikonlar tek tek. Bir efekti bütün slayta, düzleştirilmiş bir katmana ya da bir
   tablonun tamamına tek geçişte uygulamak (ekranı süpüren tarayıcı, ışık perdesi, tek maske) yasaktır.
4. **Tek efekt her şeye uygulanmaz.** Aynı slaytta başlık, kartlar, sayılar ve tablo aynı hareketle gelmez; her
   öğe türü kendine yakışan hareketi alır. Sunum boyunca da bir slaytın kahraman koreografisi bir kez kullanılır.
5. Son kare PowerPoint'in çizdiği slayttır. Her hareket o kareye oturarak biter.
6. Okuma payında (en az 2 sn) hiçbir şey kımıldamaz.
7. Kare kaçmaz, takılmaz. `slideready check` geçmeden teslim yoktur.

## 2. Bir slaytın anatomisi

| Evre | Süre (tempo 1.0) | Ne olur |
|---|---|---|
| Boş açılış | 0,3–0,6 sn | Yalnızca arka plan, hiçbir şey kımıldamaz |
| Kahraman an | 0,8–1,6 sn | Slaytın en önemli öğesinin (ya da öğe grubunun) büyük hareketi: kataloğdan biri |
| Destek | 0,4–0,7 sn/öğe | Kalan öğeler okuma sırasıyla, 60–120 ms aralıklarla, örtüşerek gelir; her tür kendi hareketiyle |
| Yerleşme | 0,2–0,4 sn | Yay fiziğiyle küçük taşma ve oturma |
| Okuma payı | 2–5 sn | Durağan. Metin arttıkça uzar |

Hareketin toplamı klibin yarısını geçmez. 6 sn'den uzun bir giriş izleyiciyi bekletir.

## 3. Hareket ilkeleri (uzman kontrol listesi)

- **Hiyerarşi:** önce en önemli şey (başlık ya da veri), sonra açıklama. Aynı anda iki kahraman olmaz.
- **Örtüşen hareket:** öğeler tek tek beklemez; bir öğe yerleşirken sonraki başlar (stagger 60–120 ms).
- **Yumuşatma:** giriş için hızlı başlayıp yavaş biten eğri (expo/quint-out). Doğrusal hareket yok.
- **Hazırlık ve devam:** büyük hareketten önce küçük bir ters kıpırtı, sonunda yay ile oturma. Ölçülü: %2–4 taşma.
- **Okuma yönü:** Türkçe soldan sağa, yukarıdan aşağı. Destek öğeleri bu sırayı izler; kahraman an bilinçli olarak
  kırabilir (merkezden dışa, aşağıdan yukarı).
- **Derinlik öğede kalır:** bir öğe uzaktan (küçük, bulanık) gelip yerine oturabilir; ama kamera ve arka plan
  sabittir.
- **Hız bulanıklığı:** hızlı her harekette yön boyunca belirgin hareket bulanıklığı olur, öğe durunca sıfıra iner.
- **Sessiz ekran yasağı:** boş açılıştan sonra 0,3 sn içinde bir şey olmaya başlar.
- **Metin okunur kalır:** metin hareket ederken bile bulanıklığı kısa sürer ve hiçbir an hareketli bir görselin
  arkasında kalmaz.

## 4. Öğe türüne göre hareket (`moves`)

Her canlandırılan slayt için `plan.json`'a `moves` yazılır: slayttaki her öğe türünün hangi hareketle geleceği.
Bir tür için tek bir sabit hareket yoktur; havuzdan seçilir. Ardışık iki slaytta aynı tür aynı hareketle gelmez
(havuzunda tek seçenek olanlar hariç). Aynı slaytta bir efekti bütün öğelere uygulama: başlık, kartlar, tablo ve
sayılar birbirinden farklı hareket eder. Işık süzmesi, parıltı gibi vurgular bir slaytta en fazla bir öğede olur.

| Tür (`moves` anahtarı) | Havuz | Ne görünür |
|---|---|---|
| `baslik` | `kelime-yukselme`, `daktilo`, `harf-araligi`, `parcacik`, `dev-olcek` | kelime kelime yükselme; harf harf yazılma; harf aralığı daralarak oturma; parçacıklardan toplanma; dev boyuttan küçülerek yerine oturma |
| `metin` | `satir-maske`, `madde-kayma`, `kelime-netlesme` | satır satır kendi alanında açılma; madde madde soldan kayma; kelime kelime bulanıktan netleşme |
| `kart` | `yay-buyume`, `domino`, `cerceve-cizim`, `ucus`, `bulusma` | tek tek yaylanarak büyüme; sırayla kendi ekseninde dönme; çerçeve çizilip içi dolma; farklı yönlerden uçup yerine oturma; iki yandan kayıp ortada buluşma |
| `tablo` | `satir-kayma`, `hucre-dalga`, `sutun-sutun` | başlık satırı önce, sonra satırlar tek tek kayar; hücreler çapraz dalgayla gelir; sütunlar soldan sağa açılır. Satır ya da hücre hiçbir an yarı kesik görünmez; tablonun tamamına tek maske yok |
| `sayi` | `odometre`, `odometre-yay` | rakam rakam, sağdan sola gecikmeli dönme; dönüp son değerde yaylanarak oturma. Bağlı çubuk ya da halka aynı eğriyle dolar |
| `grafik` | `seri-seri`, `eleman-eleman` | önce eksen ve ızgara, sonra seriler sırayla; ya da her sütun/dilim/nokta kendi gecikmesiyle. Sütun kendi tabanından büyür, çizgi veri noktalarının yolunu çizer, dilim kendi açısından açılır; değer etiketi eleman oturunca sayar. Grafiğin tamamına tarayıcı çizgisi yok |
| `ikon` | `yay-belirme`, `donerek-oturma`, `dusme` | yayla büyüyerek belirme; hafif dönerek oturma; yukarıdan düşüp yaylanma |
| `gorsel` | `murekkep`, `kenar-kayma`, `netlesme` | mürekkep yayılması gibi açılma; kenarından kayarak açılma; bulanıktan netleşme (yalnızca görselin kendisi) |
| `cizgi` | `cizilme` | ayraç, ok, bağlantı çizgisi bir uçtan öbürüne çizilir |

Logo ve dipnot gibi öğeler `static` ile sabit kalabilir.

### Giriş çeşitliliği (referans: profesyonel lansman filmleri)

İyi bir motion-graphics işinde aynı giriş iki kez görülmez: yönlü bulanıklıkla uçarak gelme, harf harf yazılma,
bulanıktan netleşme, öğenin kendi alanında maskeyle açılma, ölçekle büyüme, şekil dönüşümü, döşeme, ızgaraya oturma.
Bunlar **öğelere** uygulanır, slaytın bütününe değil.

## 5. Kahraman koreografi kataloğu

`plan.json`'da her canlandırılan slayta bir `hero` yazılır: slaytın en önemli öğesinin ya da öğe grubunun büyük
anı. Aynı `hero` sunumda bir kez kullanılır.

| `hero` | Ne görünür | En iyi olduğu slayt | Kaçın |
|---|---|---|---|
| `parcacik` | Başlık binlerce parçacıktan toplanır, harfler soldan sağa dolar | Kapak, kısa ve büyük başlık | Uzun başlık, metin yoğun slayt |
| `dev-baslik` | Başlık dev boyuttan küçülerek kendi yerine oturur, arkasından içerik öğe öğe açılır | Bölüm/ara slaytı | Çok satırlı başlık |
| `derinlik` | Kartlar uzaktan (küçük, bulanık) yerlerine uçup oturur, her biri farklı gecikmeyle | Kart/ızgara düzeni (3–8 kart) | Tek öğeli slayt |
| `domino` | Kartlar sırayla kendi ekseninde dönerek yüzünü gösterir | Süreç adımları, sıralı liste | Düzensiz yerleşim |
| `bulusma` | İki öğe grubu karşı yönlerden kayıp ortada buluşur | İki sütun, karşılaştırma, önce/sonra | Tek sütun |
| `cizim` | Önce kartların ve çizgilerin çerçeveleri çizilir, sonra içleri dolar | Diyagram, şema, çerçeveli kartlar | Fotoğraf ağırlıklı slayt |
| `tablo-dalga` | Başlık satırı iner, satırlar ya da hücreler çapraz bir dalgayla tek tek gelir, sayılar en son döner | Tablo ağırlıklı slayt | Tek satırlık tablo |
| `murekkep` | Büyük görsel mürekkep yayılması gibi açılır | Görsel ağırlıklı, az metinli slayt | Küçük görseller |
| `sayac` | Kilit sayılar tek tek, rakam rakam döner ve yaylanarak oturur; bağlı çubuk ya da halka aynı eğriyle dolar; o sırada başka büyük hareket yok | Tek ya da birkaç kilit sayı (KPI, ödül, sonuç) | Sayıların tabloda olduğu slayt |
| `grafik` | Seriler sırayla büyür, kenar parlar; değer etiketleri seri bitince belirir | Grafik ağırlıklı slayt | Çok küçük grafik |
| `daktilo` | Ana mesaj harf harf yazılır, anahtar kelime vurgulanır, ardından destek öğeleri gelir | Tek güçlü cümle, alıntı, slogan | Uzun paragraf |
| `ikon-yagmuru` | İkonlar yukarıdan düşüp yaylanarak yerlerine oturur, metinleri ardından açılır | İkonlu özellik listesi | İkonsuz slayt |
| `kapanis` | Kapanış mesajı kelime kelime gelir, son kelime vurgulanır, logo en son ve sakin | Kapanış, teşekkür | Sunum ortası |

Slayt sayısı katalogdan fazlaysa bir koreografi ancak arada en az dört slayt varsa ve öğe hareketleri, giriş yönü ve
temposu farklıysa yeniden kullanılır. `slideready check` daha yakın bir tekrarı hata, uzak bir tekrarı uyarı
sayar; uzak tekrarı da kullanıcıya raporda açıkça söyle.

## 6. Ritim

- Yoğunluk eğrisi: güçlü → orta → sakin → güçlü. Kapak ve kapanış en güçlü iki an, ama hareketleri farklıdır.
- Tempo (`tempo`) slayttan slayta 0,85–1,2 arasında değişir. Veri slaytları biraz yavaş, bölüm slaytları hızlı.
- Giriş yönü slayttan slayta değişir: art arda üç slayt aynı yönden açılmaz.

## 7. Kötü işaretler (görürsen planı değiştir)

- Kamera hareketi: slayt büyüyor, kayıyor ya da arka plan oynuyor.
- Bir tablonun, kart grubunun ya da bütün slaytın üstünden tek bir tarayıcı/ışık/maske geçmesi.
- Bir slayttaki bütün öğelerin aynı hareketle gelmesi; her slaytta aynı "yukarı kayıp netleşme".
- Bütün öğelerin aynı anda gelmesi ya da hepsinin eşit aralıkla, aynı yönden gelmesi.
- Kahraman anın 2 sn'yi geçmesi, okuma payının kısalması.
- Metnin bulanık ya da yarı saydam hâlde uzun süre kalması.
