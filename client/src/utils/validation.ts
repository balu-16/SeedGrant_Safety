import { SignupInput } from "../types";
export const validEmail = (value: string) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
export const validPhone = (value: string) =>
  /^\+?[\d\s()-]{10,18}$/.test(value.trim()) &&
  value.replace(/\D/g, "").length >= 10;
export function validateLogin(email: string, password: string) {
  return {
    ...(!validEmail(email) ? { email: "Enter a valid email address." } : {}),
    ...(password.length < 8 ? { password: "Use at least 8 characters." } : {}),
  };
}
export function validateSignup(input: SignupInput) {
  return {
    ...validateLogin(input.email, input.password),
    ...(!input.name.trim() ? { name: "Enter your full name." } : {}),
    ...(!validPhone(input.phone)
      ? { phone: "Enter a valid phone number." }
      : {}),
    ...(input.password !== input.confirm
      ? { confirm: "Passwords must match." }
      : {}),
    ...(!input.terms ? { terms: "Please accept the terms to continue." } : {}),
  };
}
