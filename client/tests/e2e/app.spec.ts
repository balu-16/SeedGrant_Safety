import { test, expect, Page } from "@playwright/test";
const browserErrors = new WeakMap<Page, string[]>();
test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
});
test.afterEach(async ({ page }) => {
  expect(browserErrors.get(page)).toEqual([]);
});
async function startLogin(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Skip", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome Back" }),
  ).toBeVisible();
}
async function login(page: Page) {
  await startLogin(page);
  await page.getByLabel("Email address", { exact: true }).fill("priya@example.com");
  await page.getByLabel("Password", { exact: true }).fill("demo12345");
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await expect(page.getByText("Hi, Priya")).toBeVisible();
}
async function close(page: Page) {
  await page.getByRole("button", { name: "Close dialog" }).click();
}
test("onboarding slides, completion and reload persistence", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Go to slide 1" }),
  ).toHaveAttribute("aria-selected", "true");
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/onboarding-1.png" });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Go to slide 2" }),
  ).toHaveAttribute("aria-selected", "true");
  await page.waitForTimeout(400);
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/onboarding-2.png" });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.waitForTimeout(400);
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/onboarding-3.png" });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Welcome Back", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Welcome Back", { exact: true })).toBeVisible();
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/login.png" });
});
test("login validation, visibility and protected routes", async ({
  page,
}) => {
  await startLogin(page);
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await expect(page.getByText("Enter a valid email address.")).toBeVisible();
  await page
    .getByLabel("Email address", { exact: true })
    .fill("priya@example.com");
  await page.getByLabel("Password", { exact: true }).fill("demo12345");
  await page
    .getByRole("button", { name: "Show password", exact: true })
    .click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveJSProperty(
    "type",
    "text",
  );
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await expect(page.getByText("Hi, Priya")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Hi, Priya")).toBeVisible();
  const storage = await page.evaluate(() =>
    localStorage.getItem("smart-safety:v1"),
  );
  expect(storage).not.toContain("demo12345");
  expect(storage).not.toContain("password");
  await page.goto("/login");
  await expect(page.getByText("Hi, Priya")).toBeVisible();
});
test("signup, edit profile, preferences, logout and navigation protection", async ({
  page,
}) => {
  await startLogin(page);
  await page.getByRole("button", { name: "Sign Up", exact: true }).click();
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/signup.png" });
  await page.getByLabel("Full name", { exact: true }).fill("Naveen Kumar");
  await page
    .getByLabel("Email address", { exact: true })
    .fill("naveen@example.com");
  await page
    .getByLabel("Phone number (+91)", { exact: true })
    .fill("+91 90000 12345");
  await page.getByLabel("Password", { exact: true }).fill("demo12345");
  await page.getByLabel("Confirm password", { exact: true }).fill("different");
  await page
    .getByRole("button", { name: "Create Account", exact: true })
    .click();
  await expect(page.getByText("Passwords must match.")).toBeVisible();
  await expect(
    page.getByText("Please accept the terms to continue."),
  ).toBeVisible();
  await page.getByLabel("Confirm password", { exact: true }).fill("demo12345");
  await page.getByRole("checkbox", { name: "Accept terms" }).click();
  await page
    .getByRole("button", { name: "Create Account", exact: true })
    .click();
  await expect(page.getByText("Hi, Naveen")).toBeVisible();
  await page.getByRole("button", { name: "Open profile", exact: true }).click();
  await page.getByRole("button", { name: "Edit Profile", exact: true }).click();
  await page.getByLabel("Full name", { exact: true }).fill("Naveen R");
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByText("Naveen R", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "App Preferences", exact: true })
    .click();
  await page.getByRole("switch", { name: "Larger text" }).click();
  await close(page);
  await page.reload();
  await page
    .getByRole("button", { name: "App Preferences", exact: true })
    .click();
  await expect(page.getByRole("switch", { name: "Larger text" })).toBeChecked();
  await close(page);
  await page.getByRole("button", { name: "Sign Out", exact: true }).click();
  await page.getByRole("button", { name: "Confirm sign out" }).click();
  await expect(page.getByText("Welcome Back", { exact: true })).toBeVisible();
  await page.goto("/profile");
  await expect(page.getByText("Welcome Back", { exact: true })).toBeVisible();
  const stored = await page.evaluate(() =>
    localStorage.getItem("smart-safety:v1"),
  );
  expect(stored).not.toContain("Naveen");
});
test("guardian changes persist and synchronize sharing counts", async ({
  page,
}) => {
  await login(page);
  await page.goto("/guardians");
  await page.getByRole("button", { name: "Add Guardian", exact: true }).click();
  await page.getByLabel("Guardian name").fill("Test Guardian");
  await page.getByLabel("Relationship").fill("Friend");
  await page.getByLabel("Guardian phone").fill("+91 90000 88888");
  await page.getByRole("button", { name: "Save guardian" }).click();
  await expect(page.getByText("4 trusted contacts connected")).toBeVisible();
  await page.reload();
  await expect(page.getByText("4 trusted contacts connected")).toBeVisible();
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/guardians.png" });
  await page.goto("/track");
  await expect(
    page.getByText("Sharing with 4 guardians", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Live Sharing", exact: true }).click();
  await page.getByRole("switch", { name: "Share live location" }).click();
  await close(page);
  await page.getByRole("tab", { name: "Home", exact: true }).click();
  await expect(page.getByText("Sharing with 0 contacts")).toBeVisible();
  await page.getByRole("tab", { name: "Guardians", exact: true }).click();
  await page.getByRole("button", { name: "Edit Test Guardian" }).click();
  await page
    .getByRole("button", { name: "Remove guardian", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Remove guardian", exact: true })
    .click();
  await expect(page.getByText("3 trusted contacts connected")).toBeVisible();
});
test("SOS cancellation, confirmation, duplicate prevention and tracking controls", async ({
  page,
}) => {
  await login(page);
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/home.png" });
  await page
    .getByRole("button", { name: "SOS — tap or hold for 3 seconds" })
    .click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByText("All Good", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "SOS — tap or hold for 3 seconds" })
    .click();
  await page.getByRole("button", { name: "Send demo SOS" }).dblclick();
  await expect(
    page.getByText("Demo alert complete", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page
    .getByRole("button", { name: "Recent Alerts", exact: true })
    .click();
  await expect(
    page.getByText("SOS simulation completed", { exact: true }),
  ).toHaveCount(1);
  await close(page);
  await page.getByRole("tab", { name: "Track", exact: true }).click();
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/track.png" });
  await page.getByRole("button", { name: "Recenter map" }).click();
  await expect(
    page.getByText("Map centered on your demo location"),
  ).toBeVisible();
  await page.getByRole("tab", { name: "History", exact: true }).click();
  await expect(page.getByText("Evening walk", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Profile", exact: true }).click();
  await page.waitForTimeout(350);
  await page.screenshot({ path: "artifacts/profile.png" });
});
test("compact and large viewports keep auth controls reachable", async ({
  page,
}) => {
  for (const [width, height] of [
    [360, 640],
    [430, 932],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await expect(
      page
        .getByRole("button", { name: "Skip", exact: true })
        .or(page.getByText("Welcome Back", { exact: true })),
    ).toBeVisible();
    if (
      await page.getByRole("button", { name: "Skip", exact: true }).isVisible()
    )
      await page.getByRole("button", { name: "Skip", exact: true }).click();
    await page.getByRole("button", { name: "Sign Up", exact: true }).click();
    await page.getByLabel("Confirm password", { exact: true }).focus();
    await page
      .getByRole("button", { name: "Create Account", exact: true })
      .scrollIntoViewIfNeeded();
    await expect(
      page.getByRole("button", { name: "Create Account", exact: true }),
    ).toBeInViewport();
    await page.waitForTimeout(350);
    await page.screenshot({ path: `artifacts/signup-${width}.png` });
    await page.getByRole("button", { name: "Sign In", exact: true }).click();
  }
});

test("horizontal onboarding gestures synchronize dots and Next", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Go to slide 1" }),
  ).toBeVisible();
  await page.mouse.move(190, 300);
  await page.mouse.wheel(390, 0);
  await expect(
    page.getByRole("button", { name: "Go to slide 2" }),
  ).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Go to slide 3" }),
  ).toHaveAttribute("aria-selected", "true");
});

test("three-second hold opens confirmation and dismissing it sends nothing", async ({
  page,
}) => {
  await login(page);
  const sos = page.getByRole("button", {
    name: "SOS — tap or hold for 3 seconds",
  });
  await sos.hover();
  await page.mouse.down();
  await page.waitForTimeout(3200);
  await page.mouse.up();
  await expect(
    page.getByText("Send an SOS alert?", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByText("All Good", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Recent Alerts", exact: true })
    .click();
  await expect(page.getByText("No alerts. You’re all good.")).toBeVisible();
});
