// Dynamic Expo config: uses EAS file secret GOOGLE_SERVICES_JSON on builders,
// falls back to local ./google-services.json for local dev.
// See: https://docs.expo.dev/eas/environment-variables/#file-environment-variables
const base = require("./app.json").expo;

module.exports = {
  expo: {
    ...base,
    android: {
      ...base.android,
      googleServicesFile:
        process.env.GOOGLE_SERVICES_JSON || "./google-services.json",
    },
  },
};
