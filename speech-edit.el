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
;; Package-Requires: ((emacs "25.1"))
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

(defun speech-edit--prompt-openai-llm (query)
  "From a user QUERY, handles the openai prompt."
  nil)

(defvar speech-edit--speech-to-text-executable "./run-speech-reco.sh")
(defvar speech-edit--speech-to-text-mock-executable "./mock-run-speech-reco.sh")
(defvar speech-edit--log-buffer-name "*speech-edit-log*")
(defvar speech-edit--transcription-buffer-name "*speech-edit-transcription*")
(defvar speech-edit--format-time-string "[%Y-%m-%d %H:%M:%S] ")
(defvar speech-edit--delay-before-sigkill 4.0)

(defvar speech-edit--transcription-process nil
  "Variable to store a handle to a running recording process")

(defun speech-edit--log-entry (type content)
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

(defun speech-edit--handle-transcription-output (output)
  "Process RESULT based on ERROR.
 Log to a temporary buffer and notify user on error."
  ;; Check if error is non-empty
  (let* ((parsed-output (json-read-from-string output))
         (result (cdr (assoc 'result parsed-output)))
         (error (cdr (assoc 'error parsed-output))))
    (if (not (string-empty-p error))
        (progn
          ;; Log the error and notify user
          (speech-edit--log-entry :error error)
          (message "Transcription error: %s" error))
      ;; If no error, log the result and return it
      (progn
        (speech-edit--log-entry :result result)
        result))))

(defun speech-edit--transcription-sentinel (proc event)
  "Sentinel function for transcription PROC. Triggered on EVENT."
  (when (buffer-live-p (process-buffer proc))
    (let ((event-type (substring event 0 -1))) ; Remove trailing newline
      (cond
       ((or (string= event-type "finished")
            (string= event-type "exited"))
        (message "Recording process finished normally."))
       ((string= event-type "killed")
        (progn
          (speech-edit--log-entry :error "Transcription process lingering. Sending SIGKILL to terminate")
          (message "Recording process killed.")))
       (t
        (progn
          (speech-edit--log-entry :error (format "Transcription process exited with unhandled process event type: %s" event-type))
          (message "Recording process ended with event: %s" event-type)))
      ;; Switch to the transcription output buffer
      (with-current-buffer (process-buffer proc)
        ;; Send content of the buffer to the transcription handler
        (speech-edit--handle-transcription-output (buffer-string))
        ;; Clean up the buffer
        (kill-buffer (current-buffer)))))))

(defun speech-edit--start-recording ()
  "Start recording and transcribing asynchronously.
Note: we ignore the output from stderr, and throw when
a transcription process was already running."
  (interactive)
  (when (process-live-p speech-edit--transcription-process)
    (error "A transcription process is already running"))
  (let ((process-buffer (get-buffer-create speech-edit--transcription-buffer-name)))
    (setq speech-edit--transcription-process (make-process
                                              :name "speech-edit-transcription"
                                              :buffer process-buffer
                                              :command (list speech-edit--speech-to-text-executable)
                                              :noquery t
                                              :stderr (make-pipe-process :name "speech-edit-transcription-stderr" :buffer nil :noquery t)
                                              :sentinel #'speech-edit--transcription-sentinel))))

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
