;;; echo-crafter.el --- Description -*- lexical-binding: t; -*-
;;
;; Copyright (C) 2023 Jean-Francois Arbour
;;
;; Author: Jean-Francois Arbour <jf.arbour@gmail.com>
;; Maintainer: Jean-Francois Arbour <jf.arbour@gmail.com>
;; Created: December 11, 2023
;; Modified: December 11, 2023
;; Version: 0.0.1
;; Keywords: data
;; Homepage: https://github.com/Jef808/EchoCrafter.git
;; Package-Requires: ((emacs "24.3"))
;;
;; This file is not part of GNU Emacs.
;;
;;; Commentary:
;;
;;  Description
;;
;;; Code:

(defvar microphone-stream nil
  "Holds the speech-to-text subprocess.")

(defvar openai-prompt-process nil
  "Holds the make-openai-prompt subprocess")

(defvar microphone-stream-buffer nil
  "Buffer for the output of the microphone stream.")

(defun start-microphone-stream ()
  "Start microphone stream subprocess."
  (interactive)
  (when (process-live-p microphone-stream)
    (error "A transcription process is already running"))
  (setq microphone-stream-buffer (generate-new-buffer "*microphone-stream output*"))
  (setq microphone-stream (start-process-shell-command "microphone-stream" microphone-stream-buffer "/home/jfa/projects/echo-crafter/run-speech-reco.sh"))
  (set-process-sentinel microphone-stream 'microphone-stream-sentinel)
  (message "Listening to microphone stream..."))

(defun stop-microphone-stream ()
  "Send SIGINT to the microphone stream subprocess."
  (interactive)
  (when (process-live-p microphone-stream)
    (interrupt-process microphone-stream)
    (message "Stopped listening to microphone stream...")))

(defun abort-microphone-stream ()
  "Send SIGKILL to the microphone stream subprocess."
  (interactive)
  (when (process-live-p microphone-stream)
    (kill-process microphone-stream)
    (message "Speech-to-text process aborted.")))

(defun microphone-stream-sentinel (process signal)
  "Handle PROCESS state change from SIGNAL description."
  (when (memq (process-status process) '(exit signal))
    (let ((exit-status (process-exit-status process)))
      (if (= exit-status 0)
          (progn
            (send-output-to-openai)
            (message "Microphone recording completed successfully, sending transcript to openai"))
        (message "Microphone stream finished with exit code %d" (process-exit-status process))))))

(defun send-output-to-openai ()
  (setq openai-prompt-process (start-process-shell-command "openai-prompt-process" "*openai-prompt output*" "/home/jfa/projects/echo-crafter/run-make-prompt.sh"))
  (set-process-sentinel openai-prompt-process 'openai-prompt-process-sentinel)
  (send-buffer-contents-to-process microphone-stream-buffer openai-prompt-process))

(defun send-buffer-contents-to-process (buffer process)
  "Send the contents of BUFFER to PROCESS."
  (with-current-buffer buffer
    (let ((contents (buffer-string)))
      (process-send-string process contents)
      (process-send-eof process))))

(defun openai-prompt-process-sentinel (process signal)
  "Handle the process state change for PROCESS upon receiving SIGNAL."
  (when (memq (process-status process) '(exit signal))
    (let ((exit-status (process-exit-status process))
          (transcript-data (with-current-buffer microphone-stream-buffer (buffer-string))))
      (if (= exit-status 0)
          (message "Openai prompt completed successfully.")
        (message "Openai prompt process terminated with exit code %d" exit-status))
      ;; Write the transcript to the output buffer
      (with-current-buffer (process-buffer process)
        (goto-char (point-min))
        (insert (format "\n\n;; Transcript:\n;; %s\n\n" transcript-data))
        (goto-char (point-min))
      ;; Kill first process buffer
      (when (buffer-live-p microphone-stream-buffer)
        (kill-buffer microphone-stream-buffer))
      ;; Show openai prompt output buffer
      (display-as-popup (process-buffer process) 'emacs-lisp-mode)))))

(defun display-as-popup (buffer-name major-mode-fn)
  "Display BUFFER-NAME as a Doom popup."
  (let ((buffer (get-buffer buffer-name))
        (current-original-buffer (current-buffer)))
    (when buffer
      (with-current-buffer buffer
        (funcall major-mode-fn)
        (setq-local +popup-window-parameters '((quit . t)))
        (setq-local original-buffer current-original-buffer)
        (setq buffer-read-only t)
        (local-set-key (kbd "C-x C-e") 'evaluate-last-sexp-in-original-buffer))
      (+popup-buffer buffer))))

(defun evaluate-last-sexp-in-original-buffer ()
  "Evaluate the last s-expression in the context of the original buffer."
  (interactive)
  (if (and (boundp 'original-buffer) (buffer-live-p original-buffer))
      (let ((last-sexp (buffer-substring (save-excursion (backward-sexp) (point)) (point))))
        (with-current-buffer original-buffer
          (eval (read last-sexp))))
    (message "Original buffer is no longer available.")))

(global-set-key (kbd "C-c r s") 'start-microphone-stream)
(global-set-key (kbd "C-c r q") 'stop-microphone-stream)
(global-set-key (kbd "C-c r a") 'abort-microphone-stream)

(provide 'echo-crafter)
;;; echo-crafter.el ends here
