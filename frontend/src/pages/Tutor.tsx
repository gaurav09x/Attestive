import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  CheckCircle2,
  Lightbulb,
  ListChecks,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Input,
  Panel,
  Select,
  Spinner,
  Textarea,
  cn,
} from "../components/ui";
import { ApiError, apiFetch } from "../lib/api";
import type {
  Subject,
  TutorConversationDetail,
  TutorConversationSummary,
  TutorReply,
  TutorStatusResponse,
} from "../lib/types";

const MODES = [
  { value: "explain", label: "Explain", icon: BookOpen },
  { value: "hint", label: "Hint", icon: Lightbulb },
  { value: "example", label: "Worked example", icon: ListChecks },
  { value: "check", label: "Check me", icon: CheckCircle2 },
] as const;

type TutorMode = (typeof MODES)[number]["value"];

export default function TutorPage() {
  const [status, setStatus] = useState<TutorStatusResponse | null>(null);
  const [conversations, setConversations] = useState<TutorConversationSummary[]>([]);
  const [active, setActive] = useState<TutorConversationDetail | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState("");
  const [mode, setMode] = useState<TutorMode>("explain");
  const [pending, setPending] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const [creating, setCreating] = useState(false);
  const [creatingBusy, setCreatingBusy] = useState(false);
  const [subjectId, setSubjectId] = useState("");
  const [topic, setTopic] = useState("");

  const threadRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiFetch<TutorStatusResponse>("/tutor/status"),
      apiFetch<{ items: TutorConversationSummary[] }>("/tutor/conversations"),
      apiFetch<{ items: Subject[] }>("/catalog/subjects?limit=50"),
    ])
      .then(async ([statusPayload, conversationPayload, subjectPayload]) => {
        if (!active) return;
        setStatus(statusPayload);
        setConversations(conversationPayload.items);
        setSubjects(subjectPayload.items);
        const first = conversationPayload.items[0];
        if (first) {
          const detail = await apiFetch<TutorConversationDetail>(
            `/tutor/conversations/${first.id}`,
          );
          if (active) setActive(detail);
        }
      })
      .catch((caught) => {
        if (!active) return;
        setError(caught instanceof ApiError ? caught.message : "Could not load the tutor.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const element = threadRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [active?.id, active?.messages.length, pending]);

  async function openConversation(id: string) {
    setError(null);
    setSuggestions([]);
    try {
      const detail = await apiFetch<TutorConversationDetail>(`/tutor/conversations/${id}`);
      setActive(detail);
      setCreating(false);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not open that session.");
    }
  }

  async function createConversation() {
    setCreatingBusy(true);
    setError(null);
    try {
      const created = await apiFetch<TutorConversationDetail>("/tutor/conversations", {
        method: "POST",
        body: JSON.stringify({
          subject_id: subjectId || null,
          topic: topic.trim() || null,
          level: "auto",
        }),
      });
      setConversations((items) => [created, ...items]);
      setActive(created);
      setCreating(false);
      setTopic("");
      setSubjectId("");
      setSuggestions([]);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not start a session.");
    } finally {
      setCreatingBusy(false);
    }
  }

  async function removeConversation(id: string) {
    setError(null);
    try {
      await apiFetch<void>(`/tutor/conversations/${id}`, { method: "DELETE" });
      setConversations((items) => items.filter((item) => item.id !== id));
      if (active?.id === id) {
        setActive(null);
        setSuggestions([]);
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not delete that session.");
    }
  }

  async function send(text?: string) {
    const content = (text ?? draft).trim();
    if (!content || !active || sending) return;
    setSending(true);
    setError(null);
    setSuggestions([]);
    setPending(content);
    setDraft("");
    try {
      const payload = await apiFetch<TutorReply>(
        `/tutor/conversations/${active.id}/messages`,
        { method: "POST", body: JSON.stringify({ content, mode }) },
      );
      setActive((current) =>
        current
          ? { ...current, ...payload.conversation, messages: [...current.messages, ...payload.messages] }
          : current,
      );
      setConversations((items) =>
        items.map((item) => (item.id === payload.conversation.id ? payload.conversation : item)),
      );
      setSuggestions(payload.suggestions);
    } catch (caught) {
      setDraft(content);
      setError(caught instanceof ApiError ? caught.message : "The tutor could not reply.");
    } finally {
      setPending(null);
      setSending(false);
    }
  }

  if (loading) return <Spinner label="Opening the tutor…" />;

  const offline = status !== null && !status.available;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">AI tutor</h1>
          <p className="mt-1 text-sm text-fog-400">
            Teaching grounded in your measured skills and this platform&apos;s curriculum.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={offline ? "rose" : "emerald"}>
            <Sparkles className="size-3" aria-hidden />
            {offline ? "Tutor offline" : `Online · ${status?.model ?? status?.provider ?? "local model"}`}
          </Badge>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setCreating(true);
              setError(null);
            }}
          >
            <Plus className="size-3.5" aria-hidden />
            New session
          </Button>
        </div>
      </header>

      {status && !status.available ? <Alert tone="error">{status.message}</Alert> : null}
      {error ? <Alert tone="error">{error}</Alert> : null}

      {creating ? (
        <Panel className="p-5">
          <h2 className="text-sm font-medium text-fog-200">Start a tutoring session</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <label className="space-y-1.5 text-xs text-fog-400">
              Subject
              <Select
                aria-label="Subject"
                value={subjectId}
                onChange={(event) => setSubjectId(event.target.value)}
              >
                <option value="">General programming</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </Select>
            </label>
            <label className="space-y-1.5 text-xs text-fog-400">
              Topic (optional)
              <Input
                aria-label="Topic"
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                placeholder="e.g. List comprehensions"
                maxLength={160}
              />
            </label>
          </div>
          <div className="mt-4 flex gap-2">
            <Button size="sm" onClick={createConversation} loading={creatingBusy}>
              Start session
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setCreating(false)}>
              Cancel
            </Button>
          </div>
        </Panel>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[17rem_1fr]">
        <Panel className="h-fit p-2">
          <p className="px-2.5 py-2 text-[11px] font-semibold tracking-[0.14em] text-fog-500 uppercase">
            Sessions
          </p>
          {conversations.length === 0 ? (
            <p className="px-2.5 pb-3 text-xs leading-relaxed text-fog-500">
              No sessions yet. Start one and ask a question about what you are studying.
            </p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conversation) => (
                <li key={conversation.id} className="group relative">
                  <button
                    type="button"
                    onClick={() => openConversation(conversation.id)}
                    className={cn(
                      "w-full rounded-lg px-2.5 py-2.5 pr-9 text-left transition-colors",
                      active?.id === conversation.id
                        ? "bg-ink-800 text-fog-100"
                        : "text-fog-400 hover:bg-ink-800/60 hover:text-fog-200",
                    )}
                  >
                    <span className="line-clamp-1 text-sm font-medium">{conversation.title}</span>
                    <span className="mt-0.5 flex items-center gap-1.5 text-[11px] text-fog-500">
                      {conversation.subject_name ?? "General"} · {conversation.message_count} messages
                    </span>
                    <span className="mt-1 line-clamp-1 block text-[11px] text-fog-500">
                      {conversation.last_message_preview || "New session"}
                    </span>
                  </button>
                  <button
                    type="button"
                    aria-label={`Delete ${conversation.title}`}
                    onClick={() => removeConversation(conversation.id)}
                    className="absolute right-1.5 top-2 rounded p-1.5 text-fog-500 opacity-0 transition-opacity hover:bg-ink-700 hover:text-rose group-hover:opacity-100 focus:opacity-100"
                  >
                    <Trash2 className="size-3.5" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel className="flex min-h-[34rem] flex-col">
          {active ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
                <div>
                  <h2 className="text-sm font-medium text-fog-100">{active.title}</h2>
                  <p className="text-[11px] text-fog-500">
                    {active.subject_name ?? "General programming"} · {active.level} level ·{" "}
                    {active.message_count} messages
                  </p>
                </div>
                <Badge tone="neutral">{active.messages.length ? "Grounded answers" : "New session"}</Badge>
              </div>

              <div ref={threadRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
                {active.messages.length === 0 && !pending ? (
                  <div className="space-y-3">
                    <p className="text-sm text-fog-400">
                      Ask about a concept, paste an error, or request a hint. The tutor sees your
                      measured skills and current roadmap step for this subject.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {[
                        "Explain this from the beginning",
                        "Give me a hint for my roadmap step",
                        "Show a small worked example",
                        "Check my understanding",
                      ].map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          onClick={() => setDraft(prompt)}
                          className="rounded-full border border-line bg-ink-850 px-3 py-1.5 text-xs text-fog-300 transition-colors hover:border-line-bright hover:text-fog-100"
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {active.messages.map((message) => {
                  const fromStudent = message.role === "user";
                  return (
                    <div
                      key={message.id}
                      className={cn("flex", fromStudent ? "justify-end" : "justify-start")}
                    >
                      <div
                        className={cn(
                          "max-w-[85%] rounded-xl border px-3.5 py-2.5",
                          fromStudent
                            ? "border-electric/30 bg-electric/10 text-fog-100"
                            : "border-line bg-ink-900/70 text-fog-200",
                        )}
                      >
                        {!fromStudent ? (
                          <div className="mb-1.5 flex items-center gap-1.5 text-[11px] text-fog-500">
                            <Sparkles className="size-3 text-violet" aria-hidden />
                            Tutor
                            {message.mode === "hint" && message.hint_level > 0 ? (
                              <span>· hint {message.hint_level}</span>
                            ) : null}
                            <span className="text-fog-600">· {message.provider}</span>
                          </div>
                        ) : null}
                        <div className="whitespace-pre-wrap text-sm leading-relaxed">
                          {message.content}
                        </div>
                        {message.sources.length > 0 ? (
                          <p className="mt-2 border-t border-line/60 pt-2 text-[11px] text-fog-500">
                            Grounded in {message.sources.slice(0, 2).join("; ")}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  );
                })}

                {pending ? (
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-xl border border-electric/20 bg-electric/5 px-3.5 py-2.5 text-sm text-fog-300">
                      {pending}
                    </div>
                  </div>
                ) : null}

                {sending ? (
                  <div className="flex items-center gap-2 text-xs text-fog-500" role="status">
                    <span className="size-1.5 animate-pulse rounded-full bg-violet" />
                    The tutor is thinking…
                  </div>
                ) : null}
              </div>

              <div className="border-t border-line px-4 py-3">
                {suggestions.length > 0 ? (
                  <div className="mb-2.5 flex flex-wrap gap-2">
                    {suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => send(suggestion)}
                        className="rounded-full border border-line bg-ink-850 px-3 py-1.5 text-xs text-fog-300 transition-colors hover:border-line-bright hover:text-fog-100"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                ) : null}

                <div className="mb-2 flex flex-wrap gap-1.5">
                  {MODES.map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => setMode(item.value)}
                      aria-pressed={mode === item.value}
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-colors",
                        mode === item.value
                          ? "border-electric/50 bg-electric/10 text-[#a9c7ff]"
                          : "border-line bg-ink-850 text-fog-400 hover:border-line-bright hover:text-fog-200",
                      )}
                    >
                      <item.icon className="size-3" aria-hidden />
                      {item.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-end gap-2">
                  <Textarea
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void send();
                      }
                    }}
                    placeholder={
                      offline
                        ? "The tutor is offline. Fix the model setup above to continue."
                        : "Ask a question, paste an error, or request a hint…"
                    }
                    className="min-h-20"
                    maxLength={2000}
                    disabled={offline || sending}
                    aria-label="Message the tutor"
                  />
                  <Button
                    onClick={() => send()}
                    loading={sending}
                    disabled={offline || !draft.trim()}
                    aria-label="Send message"
                  >
                    <Send className="size-4" aria-hidden />
                  </Button>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-fog-600">
                  Replies come from a local model and can be wrong. Graded work stays with the
                  diagnostics and roadmap, never this chat.
                </p>
              </div>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center p-6">
              <EmptyState
                icon={<MessageSquare className="size-5" aria-hidden />}
                title="Start a tutoring session"
                description="The tutor teaches from your measured skills, your active roadmap step and the platform curriculum. It never invents your scores."
                action={
                  <Button onClick={() => setCreating(true)}>
                    <Plus className="size-4" aria-hidden />
                    New session
                  </Button>
                }
              />
            </div>
          )}
        </Panel>
      </div>

      <p className="text-center text-xs text-fog-500">
        Need evidence first?{" "}
        <Link to="/assessments" className="text-fog-300 underline-offset-4 hover:underline">
          Take a diagnostic
        </Link>{" "}
        so the tutor knows what you actually know.
      </p>
    </div>
  );
}
