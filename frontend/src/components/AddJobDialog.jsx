import { useEffect, useRef, useState } from "react";
import { addManualJob } from "../api";

const EMPTY = { title: "", company: "", location: "", url: "", source: "whatsapp", description: "" };

export default function AddJobDialog({ open, onClose, onSaved }) {
  const ref = useRef(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (open && !dialog.open) {
      setForm(EMPTY);
      setError("");
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  const field = (name) => ({
    name,
    value: form[name],
    onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
  });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await addManualJob(form);
      onSaved();
    } catch (err) {
      setError(
        err.message.includes("Duplicate")
          ? "This job is already in your list."
          : `Could not save the job: ${err.message}`
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog ref={ref} onClose={onClose}>
      <form onSubmit={submit}>
        <h2>Add a job</h2>
        <label>
          Job title
          <input {...field("title")} required maxLength={300} placeholder="Junior Python Developer" />
        </label>
        <div className="two">
          <label>Company <input {...field("company")} maxLength={200} /></label>
          <label>Location <input {...field("location")} maxLength={200} /></label>
        </div>
        <label>
          Link
          <input {...field("url")} type="url" placeholder="https://" />
        </label>
        <label>
          Where did you find it?
          <select {...field("source")}>
            <option value="whatsapp">WhatsApp</option>
            <option value="linkedin">LinkedIn</option>
            <option value="manual">Other</option>
          </select>
        </label>
        <label>
          Post text
          <textarea {...field("description")} placeholder="Paste the full post here" />
        </label>
        <p className="form-error" role="alert">{error}</p>
        <div className="dlg-actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving}>Save job</button>
        </div>
      </form>
    </dialog>
  );
}
