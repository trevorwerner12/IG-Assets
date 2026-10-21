"use client";

import { useActionState, useState } from "react";
import { saveCoachProfile } from "@/app/coach/actions";
import {
  LESSON_LENGTHS,
  METRO_AREAS,
  SPECIALTIES,
  TIMEZONES,
  US_STATES,
  defaultTimezoneForState,
} from "@/lib/constants";
import type { Coach } from "@/lib/types";
import { useKeepForm } from "@/lib/use-keep-form";
import { PhotoUpload } from "./photo-upload";

/**
 * One form for both the first-time coach application (isApplication) and
 * later profile edits.
 */
export function CoachProfileForm({
  userId,
  defaultName,
  coach,
}: {
  userId: string;
  defaultName: string;
  coach: Coach | null;
}) {
  const isApplication = !coach;
  const [state, action, pending] = useActionState(saveCoachProfile, undefined);
  const onSubmit = useKeepForm(action);
  const [name, setName] = useState(coach?.display_name ?? defaultName);
  const [usState, setUsState] = useState(coach?.state ?? "");
  const [timezone, setTimezone] = useState<string>(coach?.timezone ?? "America/Phoenix");

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Section title="Your profile" note="This is what families see.">
        <PhotoUpload userId={userId} name={name} initialUrl={coach?.photo_url ?? null} />
        <Field label="Name families will see" htmlFor="display_name">
          <input
            id="display_name"
            name="display_name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="input"
          />
        </Field>
        <fieldset>
          <legend className="label">Specialties</legend>
          <div className="grid grid-cols-2 gap-2">
            {SPECIALTIES.map((s) => (
              <label
                key={s.value}
                className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-white px-3 has-[:checked]:border-navy has-[:checked]:bg-navy/5"
              >
                <input
                  type="checkbox"
                  name="specialties"
                  value={s.value}
                  defaultChecked={coach?.specialties.includes(s.value)}
                  className="h-4 w-4 accent-navy"
                />
                <span className="font-medium">{s.label}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <Field label="About you" htmlFor="bio" hint="Your coaching style and who you like to work with.">
          <textarea id="bio" name="bio" rows={5} defaultValue={coach?.bio} className="input py-2" />
        </Field>
        <Field
          label="Playing background"
          htmlFor="playing_background"
          hint="e.g. 4-year starter at Arizona State, drafted in the 12th round in 2015"
        >
          <textarea
            id="playing_background"
            name="playing_background"
            rows={3}
            defaultValue={coach?.playing_background}
            className="input py-2"
          />
        </Field>
      </Section>

      <Section title="Lessons & pricing" note="We keep 15% of each booking. The rest is paid out to you.">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Price per lesson ($)" htmlFor="lesson_price">
            <input
              id="lesson_price"
              name="lesson_price"
              type="number"
              inputMode="decimal"
              min={10}
              max={1000}
              step="1"
              defaultValue={coach ? coach.lesson_price_cents / 100 : 60}
              required
              className="input"
            />
          </Field>
          <Field label="Lesson length" htmlFor="lesson_length_minutes">
            <select
              id="lesson_length_minutes"
              name="lesson_length_minutes"
              defaultValue={coach?.lesson_length_minutes ?? 60}
              className="input"
            >
              {LESSON_LENGTHS.map((m) => (
                <option key={m} value={m}>
                  {m} minutes
                </option>
              ))}
            </select>
          </Field>
          <Field label="5-lesson pack discount (%)" htmlFor="package_5_discount_pct">
            <input
              id="package_5_discount_pct"
              name="package_5_discount_pct"
              type="number"
              inputMode="numeric"
              min={0}
              max={50}
              defaultValue={coach?.package_5_discount_pct ?? 5}
              className="input"
            />
          </Field>
          <Field label="10-lesson pack discount (%)" htmlFor="package_10_discount_pct">
            <input
              id="package_10_discount_pct"
              name="package_10_discount_pct"
              type="number"
              inputMode="numeric"
              min={0}
              max={50}
              defaultValue={coach?.package_10_discount_pct ?? 10}
              className="input"
            />
          </Field>
        </div>
      </Section>

      <Section title="Where you coach" note="Families see the facility and city. The street address is only shared after they book.">
        <Field label="Facility or field name" htmlFor="location_name" hint="e.g. Cactus Yards, Field 4">
          <input id="location_name" name="location_name" defaultValue={coach?.location_name} className="input" />
        </Field>
        <Field label="Street address" htmlFor="address">
          <input id="address" name="address" defaultValue={coach?.address} autoComplete="street-address" className="input" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="City" htmlFor="city">
            <input id="city" name="city" defaultValue={coach?.city} required autoComplete="address-level2" className="input" />
          </Field>
          <Field label="ZIP" htmlFor="zip">
            <input id="zip" name="zip" defaultValue={coach?.zip ?? ""} inputMode="numeric" maxLength={5} autoComplete="postal-code" className="input" />
          </Field>
          <Field label="State" htmlFor="state">
            <select
              id="state"
              name="state"
              value={usState}
              onChange={(e) => {
                setUsState(e.target.value);
                setTimezone(defaultTimezoneForState(e.target.value));
              }}
              required
              className="input"
            >
              <option value="">Choose…</option>
              {US_STATES.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Time zone" htmlFor="timezone">
            <select
              id="timezone"
              name="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="input"
            >
              {TIMEZONES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Field label="Metro area" htmlFor="metro_area" hint="Families search by area. Suburbs count, e.g. Katy is part of Houston.">
          <select id="metro_area" name="metro_area" defaultValue={coach?.metro_area ?? ""} required className="input">
            <option value="">Choose…</option>
            {METRO_AREAS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </Field>
      </Section>

      {isApplication && (
        <Section title="Application" note="Only our team sees this.">
          <Field label="Years coaching" htmlFor="years_coaching">
            <input id="years_coaching" name="years_coaching" type="number" inputMode="numeric" min={0} max={60} className="input" />
          </Field>
          <Field label="Certifications" htmlFor="certifications" hint="e.g. USA Baseball, CPR/First Aid, Safe Sport">
            <textarea id="certifications" name="certifications" rows={2} className="input py-2" />
          </Field>
          <Field label="References" htmlFor="references_text" hint="Two people we can contact: name, relationship, phone or email.">
            <textarea id="references_text" name="references_text" rows={3} required className="input py-2" />
          </Field>
          <Field label="Why do you want to coach with us?" htmlFor="why_join">
            <textarea id="why_join" name="why_join" rows={3} className="input py-2" />
          </Field>
          <p className="text-sm text-muted">
            By applying, you agree to a background check before your profile goes live.
          </p>
        </Section>
      )}

      {state?.error && (
        <p role="alert" className="rounded-xl bg-stitch/10 px-3 py-2 text-sm font-medium text-stitch-dark">
          {state.error}
        </p>
      )}
      {state?.message && (
        <p role="status" className="rounded-xl bg-field-light px-3 py-2 text-sm font-medium text-field">
          {state.message}
        </p>
      )}
      <button className="btn-primary w-full sm:w-auto" disabled={pending}>
        {pending ? "Saving…" : isApplication ? "Submit application" : "Save profile"}
      </button>
    </form>
  );
}

function Section({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return (
    <section className="card space-y-4 p-5">
      <div>
        <h2 className="heading text-xl">{title}</h2>
        {note && <p className="text-sm text-muted">{note}</p>}
      </div>
      {children}
    </section>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="label">
        {label}
      </label>
      {children}
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}
