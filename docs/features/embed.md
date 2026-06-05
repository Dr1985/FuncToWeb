# Embed Mode

Append `?__embed=1` to any function URL to render it without the back button, theme toggle or outer chrome, with a transparent background. Drop the URL in an `<iframe>` and the form blends into the parent site.

## Basic Usage

```html
<iframe src="http://127.0.0.1:8000/create-user?__embed=1"></iframe>
```

That's it. No server-side configuration, no separate route. Every function URL accepts `__embed=1`.

## What gets removed

In embed mode the page strips:

- The "back to index" button (multi-function mode).
- The dark/light theme toggle.
- The outer container's max-width, padding, shadow and border.
- The page background (becomes transparent).

The form itself is rendered exactly as in the standalone page — same widgets, same validation, same submit behavior.

## Combine with URL Prefill

Embed mode pairs naturally with [URL Prefill](url-prefill.md) — pass values as query params and you get a fully pre-configured embedded form:

```html
<iframe src="http://127.0.0.1:8000/edit-user?__embed=1&id=42&name=Alice"></iframe>
```

This is the recommended pattern for plugging FuncToWeb into an existing web app: open a modal with an iframe, pass the row data via URL, let FuncToWeb handle the form and validation, close the modal when done.

## Theme

The embedded form picks up the user's theme preference from `localStorage`, the same way the standalone page does. If you want to force a theme, set the preference from the parent page before loading the iframe.

## Notes

- Embed mode is purely cosmetic — validation and submit behavior are unchanged.
- File uploads, downloads and `print()` streaming all work normally inside an iframe.
