export function getOnboardingErrorMessage(err) {
  return err?.message || "Failed to confirm onboarding eligibility. Please try again.";
}

export async function submitStep1Eligibility({ chemistry, maths, physics, runOnboarding }) {
  try {
    const response = await runOnboarding({
      maths,
      physics,
      chemistry,
      preferred_branches: [],
    });

    if (response?.eligible === true && response?.onboarding_completed === true) {
      return {
        backendConfirmed: true,
        errorMsg: "",
        nextStep: 2,
        response,
      };
    }

    return {
      backendConfirmed: false,
      errorMsg: response?.message || "Eligibility was not confirmed by the backend. Please review your marks and try again.",
      nextStep: 1,
      response,
    };
  } catch (err) {
    return {
      backendConfirmed: false,
      errorMsg: getOnboardingErrorMessage(err),
      nextStep: 1,
      response: null,
    };
  }
}
