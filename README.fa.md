# AzuDl - GC2GD

**دانلودر یونیورسال عزیزی - از Google Colab به Google Drive**

AzuDl - GC2GD یک دانلودر یونیورسال مبتنی بر Google Colab است که فایل‌های پشتیبانی‌شده را مستقیم داخل Google Drive ذخیره می‌کند. این پروژه از لینک مستقیم، ویدیو و پلی‌لیست YouTube، مگنت تورنت، فایل `.torrent`، حالت تورنت خصوصی، دانلود گروهی، تاریخچه دانلود، ابزارهای مدیریت فایل، ساخت ZIP، محاسبه SHA256، مانیتورینگ وضعیت aria2، تشخیص تورنت تکراری، نمایش وضعیت زنده seeding، ادامه دانلود با aria2 session persistence و رابط گرافیکی بتا داخل Colab پشتیبانی می‌کند.

> English: [README.md](README.md)

---

## نسخه

```text
Version: 1.3.0 GUI Beta
```

---

## امکانات

- رابط گرافیکی بتا داخل Google Colab
- داشبورد تب‌بندی‌شده
- دانلود لینک مستقیم به Google Drive
- دانلود ویدیوی YouTube
- دانلود پلی‌لیست YouTube
- انتخاب کیفیت YouTube
- استخراج MP3 در حالت audio-only
- پشتیبانی از YouTube format ID سفارشی
- اصلاح خودکار فرمت‌های ویدیو-only با افزودن بهترین صدای موجود
- دانلود تورنت با magnet link
- دانلود فایل `.torrent` از URL یا مسیر محلی
- حالت تورنت خصوصی
- امکان seeding بعد از اتمام دانلود
- نمایش زنده پیشرفت دانلود تورنت
- نمایش زنده وضعیت seeding
- نمایش سرعت آپلود هنگام seeding
- نمایش حجم آپلود شده هنگام seeding
- نمایش ratio تورنت
- نمایش تعداد seeder و connection
- تشخیص تورنت تکراری با InfoHash
- ادامه یا مانیتور کردن تسک تورنت موجود به جای افزودن تکراری
- حذف خودکار تورنت تکراری در حالت error
- ذخیره session مربوط به aria2
- رفتار مناسب برای resume کردن دانلودها
- تشخیص خودکار نوع لینک
- دانلود گروهی
- تاریخچه دانلود
- لیست فایل‌های دانلود شده
- نمایش آخرین فایل دانلود شده
- گزارش فضای Google Drive
- محاسبه SHA256 برای آخرین فایل یا فایل انتخابی
- ساخت ZIP از فولدر انتخابی
- ساخت ZIP از آخرین فولدر دانلود شده
- منوی اختصاصی Torrent Tools
- بخش اطلاعات توسعه‌دهنده
- راهنمای داخلی

---

## <img src="https://img.shields.io/badge/v1.3.0-GUI%20Beta-5865F2?style=for-the-badge" alt="v1.3.0 GUI Beta">

> [!IMPORTANT]
> نسخه `1.3.0 GUI Beta` اولین رابط گرافیکی Colab را برای **AzuDl - GC2GD** اضافه می‌کند.  
> رابط کلاسیک CLI هنوز در دسترس است، اما تجربه پیش‌فرض از این نسخه به بعد GUI است.

<details>
<summary><strong>در v1.3.0 GUI Beta چه چیزی جدید است؟</strong></summary>

<br>

نسخه `1.3.0 GUI Beta` یک رابط گرافیکی مبتنی بر widgetهای Google Colab به AzuDl - GC2GD اضافه می‌کند.

این نسخه بتا همچنان workflow قدیمی CLI را نگه می‌دارد، اما یک GUI تب‌بندی‌شده اضافه می‌کند تا کاربرانی که ترجیح می‌دهند با دکمه، فرم، dropdown، checkbox و کنترل‌های تصویری کار کنند، نیازی به وارد کردن شماره منوها نداشته باشند.

هدف GUI این است که استفاده از AzuDl برای کاربران عمومی GitHub ساده‌تر شود؛ مخصوصاً کاربرانی که می‌خواهند لینک مستقیم، ویدیوی YouTube، تورنت، لینک‌های گروهی را دانلود کنند، فایل‌ها را مدیریت کنند، فضای Drive را ببینند و به ابزارهای راهنما از یک رابط دسترسی داشته باشند.

</details>

<details>
<summary><strong>ویژگی‌های GUI</strong></summary>

<br>

| بخش | اضافه‌شده در GUI Beta |
|---|---|
| Interface | رابط گرافیکی مبتنی بر widgetهای Colab |
| Navigation | چیدمان تب‌بندی‌شده |
| Dashboard | دسترسی سریع به وضعیت، فضای ذخیره‌سازی، تاریخچه و فایل‌ها |
| Auto Download | تشخیص خودکار لینک مستقیم، YouTube، magnet و torrent |
| Direct | نام فایل سفارشی، فولدر، headers و محدودیت سرعت |
| YouTube | انتخاب کیفیت، audio-only، playlist و metadata |
| Torrent | magnet، فایل `.torrent`، حالت private، seeding و aria2 status |
| Batch | چند لینک، هر لینک در یک خط |
| Files | لیست فایل‌ها، آخرین فایل و ابزارهای SHA256 |
| Archives | ساخت ZIP از فولدر و آخرین فولدر |
| Maintenance | ذخیره session، پاکسازی stopped tasks و حذف GID |
| Developer | لینک‌ها و اطلاعات پروژه و توسعه‌دهنده |
| Guide | راهنما، cookie help و PO Token help |

</details>

<details>
<summary><strong>رابط پیش‌فرض</strong></summary>

<br>

از نسخه `1.3.0 GUI Beta` به بعد، رابط پیش‌فرض برنامه GUI است.

وقتی سلول notebook به صورت عادی اجرا شود، AzuDl رابط گرافیکی Colab را اجرا می‌کند:

```python
launch_gui()
```

رابط کلاسیک CLI همچنان در دسترس است:

```python
main()
```

همچنین می‌توانید قبل از اجرای اسکریپت، حالت CLI را اجباری کنید:

```python
import os
os.environ["AZUDL_INTERFACE"] = "cli"
```

</details>

<details>
<summary><strong>تب‌های GUI</strong></summary>

<br>

```text
Dashboard
Auto
Direct
YouTube
Torrent
Batch
Files
Archives
Maintenance
Developer
Guide
```

</details>

<details>
<summary><strong>نکات نسخه بتا</strong></summary>

<br>

این نسخه یک انتشار بتا برای GUI است. موتور دانلود همچنان بر پایه همان قابلیت‌های اصلی AzuDl کار می‌کند؛ از جمله aria2، yt-dlp، ذخیره مستقیم در Google Drive، تاریخچه، ابزارهای ZIP، ابزارهای SHA256 و aria2 session persistence.

ظاهر GUI، چیدمان و تجربه کاربری ممکن است در نسخه‌های بعدی بهتر و تغییر داده شود.

</details>

<details>
<summary><strong>پیام Commit پیشنهادی</strong></summary>

<br>

```text
release: AzuDl GC2GD v1.3.0 GUI Beta
```

جایگزین:

```text
feat(gui): add Colab widget interface beta
```

</details>

---

## منوی اصلی

```text
1. Auto detect link
2. Torrent tools
3. YouTube video or playlist
4. Direct link
5. Batch download
6. Download history
7. List downloaded files
8. Storage report
9. SHA256 latest file
10. SHA256 selected file
11. ZIP folder
12. ZIP latest folder
13. Latest file
14. Developer
15. Help
16. Exit
17. Launch Colab GUI
```

---

## منوی Torrent Tools

```text
1. Torrent magnet
2. Torrent file
3. Private torrent
4. aria2 status
5. Remove aria2 GID
6. Clear stopped aria2 results
7. Save aria2 session
8. Back
```

---

## تب‌های GUI

رابط گرافیکی بتا داخل Google Colab این تب‌ها را ارائه می‌دهد:

```text
Dashboard
Auto
Direct
YouTube
Torrent
Batch
Files
Archives
Maintenance
Developer
Guide
```

| تب | کاربرد |
|---|---|
| Dashboard | دسترسی سریع به وضعیت، storage، history و ابزارهای فایل |
| Auto | تشخیص نوع لینک و دانلود لینک‌های پشتیبانی‌شده |
| Direct | دانلود لینک‌های مستقیم HTTP، HTTPS یا FTP |
| YouTube | دانلود ویدیو، پلی‌لیست، صوت، metadata و thumbnail از YouTube |
| Torrent | دانلود magnet، فایل `.torrent`، تورنت private و مدیریت seeding |
| Batch | دانلود چند لینک به صورت پشت سر هم |
| Files | لیست دانلودها، نمایش آخرین فایل و محاسبه SHA256 |
| Archives | ساخت فایل ZIP |
| Maintenance | ذخیره aria2 session، حذف GID، پاکسازی stopped tasks و بررسی storage |
| Developer | نمایش لینک‌های پروژه و توسعه‌دهنده |
| Guide | نمایش راهنما، cookie help و PO Token help |

---

## ساختار ذخیره‌سازی

AzuDl ساختار زیر را در Google Drive ایجاد می‌کند:

```text
/content/drive/MyDrive/AzuDl-GC2GD
```

```text
AzuDl-GC2GD/
├── TorrentDownloads/
├── YouTubeDownloads/
├── DirectDownloads/
├── BatchDownloads/
├── Archives/
└── Logs/
```

| فولدر | کاربرد |
|---|---|
| `TorrentDownloads` | دانلودهای magnet و `.torrent` |
| `YouTubeDownloads` | ویدیو، پلی‌لیست و صوت YouTube |
| `DirectDownloads` | دانلود لینک‌های مستقیم |
| `BatchDownloads` | خروجی دانلودهای گروهی |
| `Archives` | فایل‌های ZIP ساخته‌شده توسط AzuDl |
| `Logs` | تاریخچه، aria2 session file، قالب cookies، قالب token و فایل‌های debug |

---

## فایل aria2 Session

AzuDl اطلاعات session مربوط به aria2 را اینجا ذخیره می‌کند:

```text
/content/drive/MyDrive/AzuDl-GC2GD/Logs/aria2.session
```

این فایل کمک می‌کند aria2 بعد از restart شدن notebook، تسک‌های ناتمام را دوباره بارگذاری کند.

AzuDl از گزینه‌های زیر استفاده می‌کند:

```text
--continue=true
--always-resume=true
--save-session
--input-file
--force-save=true
```

این تنظیمات باعث می‌شوند دانلودها تا حد ممکن resume-friendly باشند.

---

## نکته مهم درباره Timeout در Google Colab

AzuDl محدودیت timeout در Google Colab را دور نمی‌زند. Google Colab ممکن است sessionهای idle یا طولانی را بر اساس سیاست‌های runtime خودش disconnect کند.

AzuDl با ذخیره aria2 session، ذخیره مستقیم فایل‌ها در Google Drive، فعال‌سازی گزینه‌های resume در aria2، تشخیص تسک‌های تورنت موجود و ادامه دادن jobهای aria2 تا حد ممکن reliability را بهتر می‌کند.

برای seeding طولانی‌مدت یا دانلود unattended، از VPS یا seedbox استفاده کنید.

---

## نوع لینک‌های پشتیبانی‌شده

AzuDl می‌تواند این موارد را به صورت خودکار تشخیص دهد:

```text
magnet:?...
https://example.com/file.zip
https://example.com/file.torrent
https://youtube.com/...
https://youtu.be/...
```

| نوع | پشتیبانی |
|---|---|
| لینک مستقیم HTTP/HTTPS | بله |
| لینک FTP | بله |
| ویدیوی YouTube | بله |
| پلی‌لیست YouTube | بله |
| magnet link | بله |
| URL فایل `.torrent` | بله |
| فایل `.torrent` محلی | بله |
| لینک‌های گروهی | بله |

---

## دانلود مستقیم

AzuDl لینک‌های مستقیم را با aria2 دانلود می‌کند.

مثال‌ها:

```text
https://example.com/file.zip
https://example.com/video.mp4
https://example.com/archive.rar
https://example.com/document.pdf
```

فیلدهای اختیاری:

- نام فولدر
- نام فایل خروجی
- محدودیت سرعت
- header سفارشی به صورت JSON

نمونه header سفارشی:

```json
{"User-Agent":"Mozilla/5.0","Referer":"https://example.com"}
```

---

## دانلود YouTube

AzuDl برای دانلود ویدیوها و پلی‌لیست‌های YouTube از `yt-dlp` استفاده می‌کند.

گزینه‌های پشتیبانی‌شده:

- بهترین کیفیت
- انتخاب کیفیت
- MP3 در حالت audio-only
- دانلود پلی‌لیست
- ذخیره metadata
- ذخیره thumbnail
- پشتیبانی از cookie file
- پشتیبانی از PO Token

مقادیر کیفیت قابل استفاده:

```text
best
4320
2160
1440
1080
720
480
360
240
144
```

---

## YouTube Cookies

بعضی دانلودهای YouTube داخل Colab ممکن است با پیام‌های authentication، age restriction یا bot-check ناموفق شوند.

راهکار پیشنهادی:

از فایل `cookies.txt` با فرمت Netscape استفاده کنید که از browser session لاگین‌شده خودتان export شده باشد.

مسیرهای قابل قبول برای cookies:

```text
/content/cookies.txt
/content/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/youtube_cookies.txt
/content/drive/MyDrive/AzuDl-GC2GD/cookies.txt
```

روش جایگزین با environment variable:

```text
AZUDL_YOUTUBE_COOKIES=/path/to/cookies.txt
```

هشدار امنیتی cookies:

```text
هیچ‌وقت cookies واقعی را منتشر، share یا commit نکنید.
```

---

## YouTube PO Token

PO Token یعنی Proof Of Origin Token. این یک گزینه پیشرفته برای `yt-dlp` و clientهای YouTube است و فقط زمانی توصیه می‌شود که anonymous access و `cookies.txt` هر دو جواب ندهند.

AzuDl مقدار PO Token را از این مسیر می‌خواند:

```text
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_po_token.txt
```

فرمت پیشنهادی خط token:

```text
mweb+YOUR_PO_TOKEN
```

مسیر اختیاری Visitor Data:

```text
/content/drive/MyDrive/AzuDl-GC2GD/Logs/youtube_visitor_data.txt
```

Environment variableها هم پشتیبانی می‌شوند:

```text
AZUDL_YOUTUBE_PO_TOKEN
AZUDL_YOUTUBE_VISITOR_DATA
AZUDL_YOUTUBE_PLAYER_CLIENT
```

---

## اصلاح صدای YouTube

بعضی فرمت‌های YouTube فقط ویدیو هستند، مخصوصاً فرمت‌های کیفیت بالا.

برای مثال:

```text
137
```

معمولاً یک فرمت video-only است.

AzuDl تلاش می‌کند بهترین صدای موجود را به آن اضافه کند:

```text
137 -> 137+ba/best
```

نمونه formatهای پیشنهادی:

```text
137+140
248+251
22
18
best
```

---

## استخراج MP3

حالت audio-only را انتخاب کنید تا خروجی به صورت زیر استخراج شود:

```text
MP3 320kbps
```

---

## دانلود تورنت

AzuDl از magnet link، URL فایل `.torrent`، فایل `.torrent` محلی، private torrent mode، seeding اختیاری، نمایش زنده پیشرفت دانلود، نمایش زنده seeding، مدیریت InfoHash تکراری و aria2 resume/session persistence پشتیبانی می‌کند.

### نمونه magnet

```text
magnet:?xt=urn:btih:EXAMPLE_HASH
```

از مسیر زیر استفاده کنید:

```text
Torrent Tools > Torrent magnet
```

### نمونه فایل torrent

```text
https://example.com/file.torrent
```

از مسیر زیر استفاده کنید:

```text
Torrent Tools > Torrent file
```

برای تورنت عمومی، از `Torrent file` استفاده کنید، نه `Private torrent`.

---

## حالت Private Torrent

حالت Private Torrent برای private trackerها طراحی شده است.

از مسیر زیر استفاده کنید:

```text
Torrent Tools > Private torrent
```

ورودی پیشنهادی:

```text
.torrent file from your private tracker
```

در حالت private این موارد غیرفعال می‌شوند:

```text
DHT
DHT6
PEX
LPD
```

این موضوع برای private trackerها مهم است، چون بسیاری از آن‌ها peer discovery عمومی را مجاز نمی‌دانند.

---

## Seeding

وقتی AzuDl می‌پرسد:

```text
Keep seeding after download? y/n
```

برای ادامه seeding بعد از دانلود، این مقدار را وارد کنید:

```text
y
```

AzuDl اطلاعات زنده seeding را نمایش می‌دهد:

```text
Upload speed
Uploaded size
Ratio
Connections
Seeders
Elapsed seeding time
```

مثال:

```text
Seeding Upload: up=1.20 MB/s, uploaded=350.40 MB, ratio=0.42, connections=8, seeders=12, time=08:31
```

Seeding فقط تا زمانی کار می‌کند که runtime کولب روشن باشد. برای seeding طولانی‌مدت از VPS، seedbox یا سرور اختصاصی استفاده کنید.

---

## چرا AzuDl برای Seeding از 525600 دقیقه استفاده می‌کند؟

بعضی buildهای aria2 مقدار زیر را قبول نمی‌کنند:

```text
seed-time=-1
```

به همین دلیل AzuDl از این مقدار استفاده می‌کند:

```text
525600
```

این یعنی 525600 دقیقه، حدود یک سال. چون Colab خیلی زودتر disconnect می‌شود، این مقدار در عمل یعنی: تا زمانی که runtime کولب روشن است seeding ادامه داشته باشد.

---

## مدیریت تورنت تکراری

AzuDl قبل از اضافه کردن فایل `.torrent`، مقدار InfoHash را می‌خواند. اگر همان تورنت از قبل در aria2 ثبت شده باشد، AzuDl تورنت موجود را تشخیص می‌دهد، GID موجود را نمایش می‌دهد، همان task را resume یا monitor می‌کند و اگر task موجود errored باشد، آن را حذف کرده و دوباره اضافه می‌کند.

---

## وضعیت aria2

از مسیر زیر استفاده کنید:

```text
Torrent Tools > aria2 status
```

این بخش موارد زیر را نمایش می‌دهد:

```text
GID
Status
Name
InfoHash
Progress
Completed size
Download speed
Upload speed
Uploaded size
Ratio
Connections
Seeders
Errors
```

---

## حذف یک Torrent Task

از مسیر زیر استفاده کنید:

```text
Torrent Tools > Remove aria2 GID
```

سپس GID نمایش داده‌شده در aria2 status را وارد کنید.

این کار زمانی مفید است که تورنت stuck، duplicated یا errored شده باشد، یا بخواهید یک seeding task را متوقف کنید.

---

## دانلود گروهی

Batch download اجازه می‌دهد چند لینک یکی‌یکی دانلود شوند.

در حالت batch این موارد پشتیبانی می‌شوند:

- لینک مستقیم
- لینک YouTube
- magnet link
- لینک `.torrent`

لینک‌های ناشناخته skip می‌شوند.

---

## تاریخچه دانلود

AzuDl تاریخچه دانلود را اینجا ذخیره می‌کند:

```text
/content/drive/MyDrive/AzuDl-GC2GD/Logs/download_history.json
```

History شامل type، source، output، status، time، format، seed mode و error message است.

---

## ابزارهای مدیریت فایل

AzuDl شامل این ابزارهاست:

```text
List downloaded files
Show latest file
Storage report
SHA256 latest file
SHA256 selected file
ZIP folder
ZIP latest folder
```

فایل‌های ZIP در این مسیر ذخیره می‌شوند:

```text
/content/drive/MyDrive/AzuDl-GC2GD/Archives
```

---

## نمونه محدودیت سرعت

```text
500K
2M
10M
```

برای بدون محدودیت گذاشتن سرعت، مقدار را خالی بگذارید.

---

## نیازمندی‌ها

AzuDl پکیج‌های مورد نیاز را داخل Colab نصب می‌کند:

```bash
apt install -y aria2 ffmpeg p7zip-full
pip install tqdm requests yt-dlp ipywidgets
```

| ابزار | کاربرد |
|---|---|
| aria2 | دانلود مستقیم، تورنت و magnet |
| ffmpeg | merge کردن YouTube و استخراج audio |
| yt-dlp | موتور دانلود YouTube |
| tqdm | progress bar |
| requests | درخواست‌های HTTP |
| ipywidgets | رابط گرافیکی Colab |
| p7zip-full | پشتیبانی از archive |

---

## روش استفاده

1. Google Colab را باز کنید: `https://colab.research.google.com`
2. یک notebook جدید بسازید.
3. کد کامل AzuDl را داخل یک cell قرار دهید.
4. cell را اجرا کنید.
5. اتصال Google Drive را authorize کنید.
6. از GUI استفاده کنید یا یک گزینه از منوی CLI انتخاب کنید.

---

## استفاده پیشنهادی

برای تورنت‌های عمومی:

```text
Torrent Tools > Torrent file
```

برای تورنت‌های private tracker:

```text
Torrent Tools > Private torrent
```

برای YouTube:

```text
YouTube video or playlist
```

برای فایل‌های مستقیم:

```text
Direct link
```

برای لینک‌های mixed:

```text
Auto detect link
```

---

## امنیت GitHub

هیچ‌وقت credentials، cookies، tokens، session files یا اطلاعات private account واقعی را commit نکنید.

موارد پیشنهادی برای `.gitignore`:

```gitignore
cookies.txt
youtube_cookies.txt
youtube_po_token.txt
youtube_visitor_data.txt
*_cookies.txt
*.cookies
*.token
aria2_rpc_secret.txt
aria2.session
```

---

## اطلاعیه قانونی

از AzuDl فقط برای محتوایی استفاده کنید که حق دانلود، ذخیره یا توزیع آن را دارید. توسعه‌دهنده مسئول سوءاستفاده از این پروژه نیست. AzuDl یک ابزار دانلودر است و مسئولیت محتوای دانلود شده بر عهده کاربر است.

---

## محدودیت‌ها

- Google Colab ممکن است هر زمان disconnect شود.
- Colab برای seeding دائمی تورنت مناسب نیست.
- بعضی لینک‌های مستقیم نیاز به authentication دارند.
- بعضی سایت‌ها IPهای Colab را block می‌کنند.
- بعضی ویدیوهای YouTube ممکن است به cookies نیاز داشته باشند یا داخل Colab در دسترس نباشند.
- seeding برای private tracker بهتر است روی VPS یا seedbox انجام شود.
- سرعت نوشتن در Google Drive ممکن است متفاوت باشد.
- GUI در وضعیت beta است و ممکن است ظاهر یا layout آن تغییر کند.

---

## توسعه‌دهنده

```text
Developer: The Azizi
Project: AzuDl - GC2GD
Full Name: Azizi Universal Downloader - Google Colab to Google Drive
```

لینک‌ها:

- X: https://x.com/the_azzi
- GitHub: https://github.com/TheGreatAzizi
- Telegram: https://t.me/luluch_code
- Git: https://git.theazizi.ir/TheAzizi
- Website: https://theazizi.ir

---

## توضیح مخزن

```text
AzuDl - GC2GD یک دانلودر یونیورسال مبتنی بر Google Colab برای دانلود لینک مستقیم، ویدیو و پلی‌لیست YouTube، magnet link، فایل torrent و private torrent مستقیم به Google Drive است و از Colab GUI beta، aria2 resume support، live progress، seeding status، batch download، history، ZIP tools و SHA256 utilities پشتیبانی می‌کند.
```

---

## پیام Commit پیشنهادی

```text
release: AzuDl GC2GD v1.3.0 GUI Beta
```

جایگزین:

```text
feat(gui): add Colab widget interface beta
```

---

## Changelog

### v1.3.0 GUI Beta

- اضافه شدن GUI beta مبتنی بر widgetهای Colab
- اضافه شدن dashboard تب‌بندی‌شده
- اضافه شدن تب‌های Auto، Direct، YouTube، Torrent، Batch، Files، Archives، Maintenance، Developer و Guide
- اضافه شدن کارت‌های Google Drive storage و usage bar در GUI
- اضافه شدن output console داخل GUI
- اضافه شدن دکمه‌ها برای actionهای رایج
- اضافه شدن دسترسی GUI به cookie help و PO Token help
- باقی ماندن CLI کلاسیک
- تنظیم GUI به عنوان رابط پیش‌فرض
- بهبود تجربه استفاده برای کاربران عمومی GitHub

### v1.2.8

- اضافه شدن تشخیص torrent InfoHash قبل از اضافه کردن فایل `.torrent`
- اضافه شدن تشخیص تورنت تکراری
- اضافه شدن resume/monitor برای aria2 torrent taskهای موجود
- اضافه شدن حذف خودکار torrent task موجود در حالت error
- بهبود خروجی aria2 status با InfoHash
- حفظ منوی اختصاصی Torrent Tools
- حفظ private torrent mode
- حفظ live seeding status
- حفظ aria2 session persistence
- حفظ YouTube audio format fix
- حفظ ZIP، SHA256، history و file tools

### v1.2.7

- رفع خطای tqdm bool هنگام نمایش وضعیت seeding

### v1.2.6

- انتقال قابلیت‌های تورنت به منوی اختصاصی Torrent Tools

### v1.2.5

- اضافه شدن live torrent seeding status
- اضافه شدن aria2 session persistence
- اضافه شدن تنظیمات resume-friendly برای aria2

### v1.2.4

- رفع مشکل invalid infinite seed-time
- جایگزینی مقدار نامعتبر `-1` با seed time طولانی و معتبر

### v1.2.3

- بهبود validation دانلود فایل `.torrent`
- بهبود پیام‌های خطای aria2 RPC

---

## License

لایسنسی را انتخاب کنید که با سیاست مخزن شما سازگار است.

گزینه‌های پیشنهادی open-source:

```text
MIT
Apache-2.0
GPL-3.0
```
