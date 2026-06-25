export class UploadStream {
  constructor({ streamUrl, onEvent, onClose, onError }) {
    this.streamUrl = streamUrl;
    this.onEvent = onEvent;
    this.onClose = onClose;
    this.onError = onError;
    this.source = null;
  }

  start() {
    this.source = new EventSource(this.streamUrl);

    const eventTypes = [
      "job_created",
      "job_started",
      "item_started",
      "download_started",
      "download_done",
      "upload_started",
      "operation_polling",
      "upload_done",
      "permission_started",
      "permission_done",
      "item_done",
      "item_failed",
      "job_done",
      "job_failed",
      "job_cancelled",
    ];

    for (const type of eventTypes) {
      this.source.addEventListener(type, (event) => {
        const data = JSON.parse(event.data);
        this.onEvent?.(data);
        if (["job_done", "job_failed", "job_cancelled"].includes(type)) {
          this.close();
          this.onClose?.(data);
        }
      });
    }

    this.source.onerror = (event) => this.onError?.(event);
  }

  close() {
    if (this.source) {
      this.source.close();
      this.source = null;
    }
  }
}
