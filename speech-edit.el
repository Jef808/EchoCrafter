;;; speech-edit.el --- Perform editing tasks from user speech -*- lexical-binding: t; -*-
;;
;; Copyright (C) 2023 Jean-Francois Arbour
;;
;; Author: Jean-Francois Arbour <jf.arbour@gmail.com>
;; Maintainer: Jean-Francois Arbour <jf.arbour@gmail.com>
;; Created: November 25, 2023
;; Modified: November 25, 2023
;; Version: 0.0.1
;; Keywords: abbrev bib c calendar comm convenience data docs emulations extensions faces files frames games hardware help hypermedia i18n internal languages lisp local maint mail matching mouse multimedia news outlines processes terminals tex tools unix vc wp
;; Homepage: https://github.com/jfa/speech-edit
;; Package-Requires: ((emacs "27.1"))
;;
;; This file is not part of GNU Emacs.
;;
;;; Commentary:
;;
;;  Perform editing tasks from user speech
;;
;;; Code:

(require 'url)
(require 'json)

(defvar speech-edit--query-queue '()
  "Queue for queries to be processed through openai API")

(defun speech-edit--prompt-openai-llm (query)
  "From a user QUERY, handles the openai prompt."
  (message "Processing query %s" query))

(defvar speech-edit--speech-to-text-executable "./mock-run-speech-reco.sh"
  "Executable to speech-to-text executable")
(defvar speech-edit--log-buffer-name "*speech-edit-log*"
  "Buffer to collect logs.")
(defvar speech-edit--format-time-string "[%Y-%m-%d %H:%M:%S] "
  "Format for timestamps in log buffer.")
(defvar speech-edit--delay-before-sigkill 4.0
  "Seconds for which to wait before we send SIGKILL when termination hangs.")
(defvar speech-edit--transcription-process nil
  "Variable to store a handle to a running recording process.")
(defvar speech-edit--transcription-buffer-name "*speech-edit-transcription*"
  "Buffer to capture the transcription subprocess output.")

(defun speech-edit--add-log-entry (type content)
  "Log CONTENT based on TYPE (:error or :transcript) to a logging buffer."
  ;; Note the timestamp immediately on call
  (let ((timestamp (format-time-string speech-edit--format-time-string)))
    ;; Create buffer if it doesn't exist and switch to it
    (with-current-buffer (get-buffer-create speech-edit--log-buffer-name)
      ;; Make sure point is at the end of content
      (goto-char (point-max))
      ;; Insert newline if not at the first column
      (unless (eq (current-column) 0)
        (insert "\n"))
      ;; Log the content based on type
      (let ((prefix (cond
                     ((eq type :error) "[ERROR]")
                     ((eq type :result) "[TRANSCRIPT]"))))
      (insert (format "%s: %s: %s\n" timestamp prefix content))))))

(defun speech-edit--collect-metadata ()
  "Collect and return metadata which will accompany the transcribed speech"
  (let ((timestamp (time-convert (current-time) 'integer))
        (buffer-name (buffer-name))
        (point-pos (point))
        (region-start (if (use-region-p) (region-beginning) nil))
        (region-end (if (use-region-p) (region-end) nil)))
    (let ((region-content (if (and region-start region-end) (buffer-substring-no-properties region-start region-end))))
      (list :timestamp timestamp
            :buffer buffer-name
            :point point-pos
            :region-start region-start
            :region-end region-end
            :region-content region-content))))

(defun speech-edit--handle-process-termination (event)
  "Handle/log PROC termination EVENT.
Return t if process terminated gracefully, nil otherwise."
  (let ((event-type (substring event 0 -1))) ; Remove trailing newline
    (cond
     ((or (string= event-type "finished")
          (string= event-type "exited"))
      (message "Recording process finished normally.")
      t)
     ((string= event-type "killed")
      (progn
        (speech-edit--add-log-entry :error "Transcription process lingering. Sending SIGKILL to terminate")
        (message "Recording process killed."))
      nil)
     (t
      (progn
        (speech-edit--add-log-entry :error (format "Transcription process exited with unhandled process event type: %s" event-type))
        (message "Recording process ended with event: %s" event-type))
      nil))))

(defun speech-edit--handle-speech-to-text-output (proc)
  (let ((output (with-current-buffer (process-buffer proc)
                  (buffer-string))))
    (let ((parsed-output (json-read-from-string output)))
      (let ((result (cdr (assoc 'result parsed-output)))
            (error (cdr (assoc 'error parsed-output))))
        (if (not (string-empty-p error))
          ;; If error, log it and notify user
          (progn
            (speech-edit--add-log-entry :error error)
            (message "Transcription error: %s" error)
            "")
          ;; If no error, log the result and return it
          (progn
            (speech-edit--add-log-entry :result result)
            result))))))

(defun speech-edit--enqueue-query (query metadata)
  "Add QUERY along with METADATA to the processing queue."
  (push (cons :query query) metadata) speech-edit--query-queue
  (message "Enqueued query %s" query))

(defun speech-edit--start-recording ()
  "Start recording and transcribing asynchronously.
Note: we ignore the output from stderr, and throw when
a transcription process was already running."
  (interactive)
  (when (process-live-p speech-edit--transcription-process)
    (error "A transcription process is already running"))
  (let ((metadata (speech-edit--collect-metadata)))
    (setq speech-edit--transcription-process (make-process
                                              :name "speech-edit-transcription"
                                              :command (list speech-edit--speech-to-text-executable)
                                              :noquery t
                                              :stderr (make-pipe-process :name "speech-edit-transcription-stderr" :buffer nil :noquery t)
                                              :sentinel (lambda (proc event)
                                                          (and
                                                           (when (speech-edit--handle-process-termination event)
                                                             (let ((transcript (speech-edit--handle-speech-to-text-output proc)))
                                                               (and (not (string-empty-p transcript))
                                                                    (speech-edit--enqueue-query transcript metadata)))
                                                             (kill-buffer (process-buffer proc)))))))))


(defun speech-edit--stop-recording ()
  "Stop the recording process."
  (interactive)
  (when (process-live-p speech-edit--transcription-process)
    (interrupt-process speech-edit--transcription-process)
    ;; Wait for a short duration to allow process to terminate
    (sleep-for speech-edit--delay-before-sigkill)
    (if (process-live-p speech-edit--transcription-process)
        (progn
          (kill-process speech-edit--transcription-process)
          (message "Transcription process did not terminate on SIGINT, sending SIGKILL."))
      (message "Recording stopped."))
    (setq speech-edit--transcription-process nil))
  (unless (process-live-p speech-edit--transcription-process)
    (message "No recording process is running.")))


(provide 'speech-edit)
;;; speech-edit.el ends here
