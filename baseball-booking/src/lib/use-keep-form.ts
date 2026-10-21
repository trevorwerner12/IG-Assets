"use client";

import { startTransition, type FormEvent } from "react";

/**
 * React clears a form after a server action finishes. Submitting through this
 * handler instead keeps what the user typed, so an error doesn't wipe a long form.
 */
export function useKeepForm(dispatch: (formData: FormData) => void) {
  return (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    startTransition(() => dispatch(formData));
  };
}
