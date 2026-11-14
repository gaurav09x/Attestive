import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { KeyRound, LogOut, UserRound, GraduationCap } from "lucide-react";
import { Alert, Badge, Button, Field, Input, Panel, Spinner, Textarea } from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatDate, formatMinutes, humanize } from "../lib/format";
import type { MeResponse, User } from "../lib/types";

export default function Settings() {
  const { user, setUser, logout } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [headline, setHeadline] = useState(user?.profile?.headline ?? "");
  const [bio, setBio] = useState(user?.profile?.bio ?? "");
  const [targetRole, setTargetRole] = useState(user?.profile?.target_role ?? "");
  const [weeklyGoal, setWeeklyGoal] = useState(user?.profile?.weekly_minutes_goal ?? 300);
  const [timezone, setTimezone] = useState(
    user?.profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone,
  );

  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    let active = true;
    apiFetch<MeResponse>("/users/me")
      .then((payload) => {
        if (!active) return;
        setMe(payload);
        setFullName(payload.user.full_name);
        setHeadline(payload.user.profile?.headline ?? "");
        setBio(payload.user.profile?.bio ?? "");
        setTargetRole(payload.user.profile?.target_role ?? "");
        setWeeklyGoal(payload.user.profile?.weekly_minutes_goal ?? 300);
        setTimezone(payload.user.profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone);
      })
      .catch((caught) => {
        if (active) setLoadError(caught instanceof ApiError ? caught.message : "Could not load your profile.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError(null);
    setProfileSaved(false);

    if (fullName.trim().length < 2) {
      setProfileError("Please enter your full name.");
      return;
    }
    if (weeklyGoal < 30 || weeklyGoal > 3000) {
      setProfileError("Weekly goal must be between 30 and 3000 minutes.");
      return;
    }

    setSavingProfile(true);
    try {
      const updated = await apiFetch<User>("/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          full_name: fullName.trim(),
          headline: headline.trim(),
          bio: bio.trim(),
          target_role: targetRole.trim(),
          weekly_minutes_goal: weeklyGoal,
          timezone,
        }),
      });
      setUser(updated);
      setMe((current) => (current ? { ...current, user: updated } : current));
      setProfileSaved(true);
    } catch (caught) {
      setProfileError(caught instanceof ApiError ? caught.message : "Could not save your profile.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function savePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSaved(false);

    if (newPassword.length < 8 || !/[A-Za-z]/.test(newPassword) || !/\d/.test(newPassword)) {
      setPasswordError("New password must be at least 8 characters and include a letter and a number.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    setSavingPassword(true);
    try {
      await apiFetch<{ message: string }>("/users/me/password", {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      setPasswordSaved(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (caught) {
      setPasswordError(caught instanceof ApiError ? caught.message : "Could not update your password.");
    } finally {
      setSavingPassword(false);
    }
  }

  if (loading) return <Spinner label="Loading your profile…" />;

  if (loadError || !me) {
    return (
      <Panel className="mx-auto max-w-lg p-8 text-center">
        <h1 className="text-lg font-semibold">Profile unavailable</h1>
        <p className="mt-2 text-sm text-fog-400">{loadError ?? "Please sign in again."}</p>
        <Link to="/login" className="mt-5 inline-block">
          <Button>Go to sign in</Button>
        </Link>
      </Panel>
    );
  }

  const profile = me.user.profile;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <header>
        <h1 className="text-2xl font-semibold">Profile & settings</h1>
        <p className="mt-1 text-sm text-fog-400">
          Keep your goals current. Your roadmap and recommendations use this information.
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          <Panel className="p-5">
            <div className="flex items-center gap-2 text-sm font-medium text-fog-200">
              <UserRound className="size-4 text-electric" aria-hidden />
              Personal details
            </div>

            <form onSubmit={saveProfile} className="mt-5 space-y-4">
              {profileError ? <Alert>{profileError}</Alert> : null}
              {profileSaved ? <Alert tone="success">Profile updated.</Alert> : null}

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Full name" htmlFor="settings-name">
                  <Input
                    id="settings-name"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    maxLength={120}
                  />
                </Field>
                <Field label="Target role" htmlFor="settings-role" optional>
                  <Input
                    id="settings-role"
                    value={targetRole}
                    onChange={(event) => setTargetRole(event.target.value)}
                    placeholder="Backend Engineer"
                    maxLength={120}
                  />
                </Field>
              </div>

              <Field label="Headline" htmlFor="settings-headline" optional hint="One line about what you're working toward.">
                <Input
                  id="settings-headline"
                  value={headline}
                  onChange={(event) => setHeadline(event.target.value)}
                  maxLength={140}
                  placeholder="Learning backend engineering"
                />
              </Field>

              <Field label="About you" htmlFor="settings-bio" optional>
                <Textarea
                  id="settings-bio"
                  value={bio}
                  onChange={(event) => setBio(event.target.value)}
                  maxLength={2000}
                  placeholder="What you already know, what you want to build, and how much time you have."
                />
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Weekly study goal (minutes)" htmlFor="settings-goal" hint="30–3000 minutes">
                  <Input
                    id="settings-goal"
                    type="number"
                    min={30}
                    max={3000}
                    step={30}
                    value={weeklyGoal}
                    onChange={(event) => setWeeklyGoal(Number(event.target.value))}
                  />
                </Field>
                <Field label="Timezone" htmlFor="settings-tz">
                  <Input
                    id="settings-tz"
                    value={timezone}
                    onChange={(event) => setTimezone(event.target.value)}
                    maxLength={64}
                  />
                </Field>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <Button type="submit" loading={savingProfile}>
                  Save changes
                </Button>
                <span className="text-xs text-fog-500">Email cannot be changed in Phase 1.</span>
              </div>
            </form>
          </Panel>

          <Panel className="p-5">
            <div className="flex items-center gap-2 text-sm font-medium text-fog-200">
              <KeyRound className="size-4 text-violet" aria-hidden />
              Password
            </div>
            <p className="mt-1 text-xs text-fog-500">
              Changing your password signs out every other session.
            </p>

            <form onSubmit={savePassword} className="mt-5 space-y-4">
              {passwordError ? <Alert>{passwordError}</Alert> : null}
              {passwordSaved ? <Alert tone="success">Password changed. Other sessions are signed out.</Alert> : null}

              <Field label="Current password" htmlFor="current-password">
                <Input
                  id="current-password"
                  type="password"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  required
                />
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="New password" htmlFor="new-password" hint="8+ characters, a letter and a number">
                  <Input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    required
                  />
                </Field>
                <Field label="Confirm new password" htmlFor="confirm-new-password">
                  <Input
                    id="confirm-new-password"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                  />
                </Field>
              </div>

              <Button type="submit" variant="secondary" loading={savingPassword}>
                Update password
              </Button>
            </form>
          </Panel>
        </div>

        <div className="space-y-5">
          <Panel className="p-5">
            <div className="flex items-center gap-2 text-sm font-medium text-fog-200">
              <GraduationCap className="size-4 text-electric" aria-hidden />
              Learning profile
            </div>

            <dl className="mt-4 space-y-3 text-sm">
              {[
                ["Education", humanize(profile?.education_level)],
                ["Experience", humanize(profile?.experience_level)],
                ["Career goal", humanize(profile?.career_goal)],
                ["Preferred style", humanize(me.user.preferences?.learning_style)],
                ["Session length", `${me.user.preferences?.session_minutes ?? "—"} min`],
                ["Weekly goal", formatMinutes(profile?.weekly_minutes_goal ?? 0)],
              ].map(([label, value]) => (
                <div key={label} className="flex items-start justify-between gap-3">
                  <dt className="text-fog-500">{label}</dt>
                  <dd className="text-right text-fog-200">{value}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-5 border-t border-line pt-4">
              <p className="text-[11px] uppercase tracking-[0.12em] text-fog-500">Subjects</p>
              {me.interests.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {me.interests.map((subject) => (
                    <Badge key={subject.id} tone="blue">
                      {subject.name}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-xs text-fog-500">No subjects selected yet.</p>
              )}
            </div>

            <Link
              to={profile?.onboarding_completed_at ? "/onboarding?edit=1" : "/onboarding"}
              className="mt-5 inline-flex text-xs font-medium text-electric hover:underline"
            >
              {profile?.onboarding_completed_at ? "Update learning preferences" : "Complete onboarding"}
            </Link>
          </Panel>

          <Panel className="p-5">
            <h2 className="text-sm font-medium text-fog-200">Account</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex items-start justify-between gap-3">
                <dt className="text-fog-500">Email</dt>
                <dd className="break-all text-right text-fog-200">{me.user.email}</dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-fog-500">Member since</dt>
                <dd className="text-fog-200">{formatDate(me.user.created_at)}</dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-fog-500">Role</dt>
                <dd className="text-fog-200">{humanize(me.user.role)}</dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-fog-500">XP</dt>
                <dd className="text-fog-200">{me.user.xp_total}</dd>
              </div>
            </dl>

            <Button
              variant="danger"
              className="mt-5 w-full"
              onClick={() => {
                void logout();
              }}
            >
              <LogOut className="size-4" aria-hidden />
              Sign out
            </Button>
          </Panel>

          <p className="px-1 text-[11px] leading-relaxed text-fog-600">
            Attestive stores only what it needs to teach you. Passwords are hashed with Argon2id and
            refresh tokens are stored as SHA-256 fingerprints.
          </p>
        </div>
      </div>
    </motion.div>
  );
}
