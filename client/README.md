# Smart Safety Tag

A local Android-first Expo / React Native / TypeScript prototype matching the supplied safety-app references. It includes three onboarding cards, Login, Sign Up, Home, Track + History, Guardians, and Profile.

## Run

Use Node.js 22 LTS or newer and npm. Development was verified with Node 24.21.0, npm 11.19.0 and Expo SDK 57.

```sh
npm install
npx expo start
```

Open the project in an Expo Go version compatible with SDK 57, or press `a` with an Android emulator configured. For the browser preview:

```sh
npm run web
```

The development preview runs at `http://localhost:8081`. With no configuration the app runs fully offline as a demo (no API keys, backend, or external accounts needed). Set `EXPO_PUBLIC_API_URL` (e.g. in a `.env` file or an EAS secret) to connect to the Smart Safety Tag server: auth, guardians, SOS, push and realtime events then go through the API, while the demo flows stay available as fallbacks.

## Try the demo

1. Swipe or use Next through the three onboarding cards. Skip and completion both lead to Login. Onboarding completion survives reopening.
2. Sign in using any valid email and a password of at least eight characters, or use the mock Google button. Sign Up validates name, email, phone, matching passwords and terms acceptance.
3. On Home, tap SOS or hold it for three seconds, then confirm or cancel. Confirmation adds one simulated alert to Recent Alerts. No real messages or calls are sent.
4. In Track, switch Live / History, recenter the illustrated map, and pause or resume sharing. Guardian counts update across Home, Track and Profile.
5. Add, edit, designate a primary, or remove a guardian. Demo mode stores changes locally; backend mode records the invite on the server (guardians identify themselves by email and accept from their own Guardian tab).
6. Edit your profile and preferences. Sign Out clears your profile, custom guardians, preferences, and session alerts, while retaining onboarding completion.

Mock locations, BLE/device connection, sharing, permissions, emergency delivery, voice help, and notifications are demonstrations. The app never reads real GPS, contacts or microphone data. Notification and permission switches save demo preferences without requesting OS access.

The Forgot Password flow produces a local confirmation and does not send email. Passwords are never persisted or logged. The Google action signs into the fictional Priya demo profile without contacting Google.

## Artwork

The original nine reference images remain unchanged in `reference/`.

| Asset | Use |
| --- | --- |
| `assets/illustrations/onboarding-1.png` | Card 1; cropped for Login and Sign Up |
| `assets/illustrations/onboarding-2.png` | Location-sharing card |
| `assets/illustrations/onboarding-3.png` | SOS card |
| `assets/illustrations/guardians.png` | Guardians hero |
| `assets/avatars/demo-profile.png` | Fictional demo profile photo |
| `assets/brand/icon.svg` | Code-native shield/heart brand icon |

All three onboarding illustrations show open eyes and plain backpack straps with no tag, clip or hanging tracker. Card 2's extra hand was corrected during generation. The same character and illustration style are used across onboarding and authentication. Standalone device imagery remains on Home and Profile.

The raster artwork was generated with the built-in image tool. Exact prompts and the corrective pass are recorded in `assets/illustrations/PROMPTS.md` and `assets/illustrations/SUPPORTING-PROMPTS.md`. These are illustration assets, not full UI screenshots. Text, forms, buttons, cards, waves, map controls, and navigation are real components. Custom guardian contacts use initials as local avatar fallbacks.

## Project structure

- `src/app/`: Expo Router routes, guarded auth stack and four tabs.
- `src/features/`: screen compositions grouped by feature.
- `src/components/`: shared UI primitives, header and device card.
- `src/constants/`: theme and illustration references.
- `src/services/`: typed service contracts with `mock.ts` implementations, `remote/` API-backed implementations, and the mock/remote selector in `index.ts` (auth always goes remote when `EXPO_PUBLIC_API_URL` is set).
- `src/hooks/`: screen-facing service hooks (auth, data, realtime, push) built on top of the service layer.
- `src/store/`: Context/reducer and versioned AsyncStorage persistence.
- `src/types/` and `src/utils/`: shared models and validation.
- `tests/`: state/validation tests and Playwright interaction tests.

The single storage key is `smart-safety:v1`. It persists onboarding completion, the minimal profile, guardians and preferences. Sharing state and simulated alert history last for the current app session. Stored data is validated on hydration; invalid or unreadable storage falls back to a usable demo. No backend migration is needed for this version.

## Checks

```sh
npm run typecheck
npm run lint
npm test
npx expo install --check
npx expo-doctor
npx playwright install chromium
npm run test:e2e
npx expo export --platform android --output-dir dist/android
npx expo export --platform web --output-dir dist/web
```

Playwright starts or reuses the local Expo web server. Tests cover onboarding navigation and gestures, auth validation, visibility and reset, session restoration, protected routes, profile editing, persistence, logout, guardian CRUD and counts, sharing, SOS cancellation/confirmation/duplicate prevention, three-second hold, history/recentering, and compact/large auth layouts. Browser console errors fail the tests. Screenshots are saved in the ignored `artifacts/` folder.

Verified mobile browser viewports: 360 × 640, 390 × 844, and 430 × 932. Android bundling succeeds; an Android SDK/device/emulator was not available in this workspace, so native keyboard, physical swipe, TalkBack, and Android hardware-back behavior still need a device pass. All screens use safe areas; forms scroll and avoid the keyboard, and dialogs handle native back dismissal.

The original templates' unused dependencies have been removed. `xcode`'s transitive UUID dependency is pinned to compatible CommonJS version 11.1.1 to address its audit advisory. npm still reports three moderate entries for the remaining `expo-router → query-string → decode-uri-component` advisory chain ([upstream advisory](https://github.com/advisories/GHSA-vcc3-ghjq-m6fr)). The available decoder fix changes CommonJS to ESM and is not forced into Expo Router's dependency chain. There are no high or critical audit findings. Review the upstream fix before using this prototype in production.
