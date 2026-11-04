# doxgen-worker

## Security

The worker renders templates that API users upload. It must run on an internal network that only the doxgen API can reach.

- Set `WORKER_TOKEN` to the same value as the API's `WORKER_TOKEN`. The worker does not start without it, and it answers `401` to a generation request without `Authorization: Bearer <WORKER_TOKEN>`.
- `template_path` and `destination_path` must stay under `/storage`. Other paths get `400`.
- appy expressions run through RestrictedPython. Templates cannot import documents, images or other templates from a path or a URL. Templates with macros, linked sections, external data, DDE or formulas that fetch URLs get `400`.
- `soffice` listens for UNO connections on `127.0.0.1` only.
