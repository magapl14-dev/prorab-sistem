# WELL DOM — мобильное приложение (Capacitor)

Нативное Android + iOS приложение, оборачивающее веб-фронтенд из `../frontend/`.
Тот же UI, те же данные, тот же backend на `https://welldom05.duckdns.org`.

## Что нужно установить

| Платформа | Требования |
|---|---|
| Любая сборка | Node.js 18+, npm |
| Android APK | Android Studio (Hedgehog 2023.1+) + JDK 17 + Android SDK 34 |
| iOS IPA | **Только на macOS**: Xcode 15+ + Apple Developer аккаунт ($99/год) |

## Первый запуск (один раз)

```bash
cd mobile
npm install

# Сгенерировать Android проект (создаст mobile/android/)
npm run init:android

# (Только на Mac) сгенерировать iOS проект
npm run init:ios
```

После `init:android` нужно вручную поправить **`mobile/android/app/src/main/AndroidManifest.xml`** —
добавить разрешения для камеры, микрофона, push, сети. Заготовка:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
<uses-feature android:name="android.hardware.camera" android:required="false" />
<uses-feature android:name="android.hardware.microphone" android:required="false" />
```

Для iOS — в **`mobile/ios/App/App/Info.plist`** добавить:

```xml
<key>NSCameraUsageDescription</key>
<string>Чтобы прикреплять фото чеков и работ к записям</string>
<key>NSMicrophoneUsageDescription</key>
<string>Чтобы записывать голосовые заметки и заполнять формы голосом</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Чтобы выбирать фото из галереи</string>
```

## Регулярная разработка

После любой правки в `../frontend/` нужно засинкать веб-код в Capacitor:

```bash
# Открыть в Android Studio (там Run/Debug → выбрать устройство)
npm run open:android

# Открыть в Xcode на Mac
npm run open:ios

# Собрать debug APK (быстро, для тестов)
npm run build:android:debug
# → mobile/android/app/build/outputs/apk/debug/app-debug.apk

# Собрать release APK (для публикации, нужен подпись)
npm run build:android
```

## Иконки и splash screen

Подготовь один файл `1024x1024 PNG` с лого. Положи как `mobile/resources/icon.png` и `mobile/resources/splash.png` (2732×2732), потом:

```bash
npm install -g @capacitor/assets
npx @capacitor/assets generate
```

Это сгенерит все нужные размеры для Android и iOS.

## Подпись релиза для Google Play

```bash
keytool -genkey -v -keystore welldom-release.keystore -alias welldom -keyalg RSA -keysize 2048 -validity 10000
```

Сохрани `welldom-release.keystore` в надёжном месте — **без этого ключа нельзя обновлять приложение в сторе**.

Создай `mobile/android/keystore.properties`:
```
storeFile=../../welldom-release.keystore
storePassword=ТВОЙ_ПАРОЛЬ
keyAlias=welldom
keyPassword=ТВОЙ_ПАРОЛЬ_КЛЮЧА
```

В `mobile/android/app/build.gradle` Capacitor уже умеет это подхватить.

## Что внутри (тебе для понимания)

- `capacitor.config.json` — `appId`, `appName`, splash, status bar
- `sync-web.js` — копирует `../frontend/*` в `www/` перед каждой сборкой
- `package.json` — Capacitor плагины: camera, filesystem, network, preferences, push, splash, status bar
- `android/` — генерится `npm run init:android` (в .gitignore)
- `ios/` — генерится `npm run init:ios` на Mac (в .gitignore)

## Frontend знает что это нативка

В `frontend/api.js` уже есть детект:
```js
const isCap = window.Capacitor?.isNativePlatform?.() === true || /^capacitor:/i.test(window.location.protocol);
if (isCap) return "https://welldom05.duckdns.org/api/v1";
```

Так что нативное приложение всегда стучит на продакшн-API, а веб-версия использует относительные пути.

## Публикация в стор — порядок шагов

### Google Play
1. Зарегистрировать аккаунт разработчика ($25 разово) → https://play.google.com/console
2. Создать приложение в консоли, заполнить описание, скриншоты
3. Сгенерировать ключ подписи (выше)
4. `npm run build:android` → получить `app-release.aab` (Android App Bundle)
5. Загрузить .aab в Play Console → выбрать canal → отправить на review (1-3 дня)

### App Store
1. Зарегистрировать Apple Developer аккаунт ($99/год) → https://developer.apple.com
2. Создать App ID в Apple Developer portal
3. На Mac: `npm run open:ios` → в Xcode выбрать team, signing & capabilities
4. Product → Archive → загрузить через Xcode Organizer
5. В App Store Connect заполнить описание, скриншоты, отправить на review (1-3 дня)

## FAQ

**Можно ли тестировать без публикации?**
Да — debug APK устанавливается через USB на любой Android. На iOS — через TestFlight (бесплатно, до 100 тестировщиков).

**Будут ли работать камера/микрофон/push?**
Да, через плагины Capacitor. Видео-запись звука через MediaRecorder (уже используется в коде) тоже работает.

**Что с обновлениями?**
Маленькие правки веб-фронта не требуют переотправки в стор — backend отдаёт свежие JS/HTML, WebView подхватывает. Только если меняешь нативный код (новый плагин) — нужна новая версия в стор.

**Размер APK?**
~5-8 MB (Capacitor + плагины). Без раздутости как у RN-приложений.
