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

(defun speech-edit--speech-reco-output-handler (process output)
  "Handle OUTPUT from the PROCESS."
  (when (buffer-live-p (process-buffer process))
    (with-current-buffer (process-buffer process)
      (goto-char (point-max))
      (insert output))))

(defun speech-edit--speech-reco-sentinel (process event)
  "Handle EVENT for the PROCESS."
  (when (string-match-p "finished\\|exited" event)
    (message "Transcription finished")))

(defun speech-edit--run-speech-reco ()
  "Run the speech-reco script asyncronously."
  (let ((process (make-process :name "speech-reco"
                               :buffer "*speech-reco-output*"
                               :command '("python3" "./speech-reco.py")
                               :filter #'speech-edit--speech-reco-output-handler
                               :sentinel #'speech-edit--speech-reco-sentinel)))
    (message "Started speech-reco script: %s" (process-name process))))

(defun generate-emacs-lisp-code (api-key emacs-environment user-query callback)
  (let ((url-request-method "POST")
        (url-request-extra-headers `(("Content-Type" . "application/json")
                                     ("Authorization" . ,(concat "Bearer " api-key))))
        (url-request-data
         (json-encode `(("model" . "gpt-4.0")
                        ("prompt" . ,(concat "Format your response as a JSON object with two fields. "
                                             "The first field, 'needs_clarification', should be a boolean indicating whether further clarification or information about the current Emacs state is needed. "
                                             "The second field, 'response_content', should contain the content of the response, either the Emacs-Lisp code or the clarification question. Here's the query:\n\n"
                                             "Emacs Environment: " emacs-environment "\n"
                                             "User Query: " user-query "\n\n"
                                             "Response:"))
                        ("temperature" . 0.5)
                        ("max_tokens" . 250)))))
    (url-retrieve "https://api.openai.com/v1/completions"
                  (lambda (_status)
                    ;; Process the response
                    (goto-char url-http-end-of-headers)
                    (let* ((json-object-type 'alist)
                           (json-array-type 'list)
                           (json-false nil)
                           (response (json-read-from-string (buffer-substring-no-properties (point) (point-max)))))
                      (funcall callback response))
                    (kill-buffer))
                  nil t)))

(defun my-callback (response)
  "Callback function to handle the response."
  (message "Generated Response (JSON): %s" (json-encode response)))

(defun example-use-of-generate-emacs-lisp-code ()
  (let ((api-key "your-api-key")  ; Replace with your actual OpenAI API key
        (emacs-environment "The cursor is currently inside a defun block named 'process-data', which takes two arguments. The buffer contains typical Lisp code structure.")
        (user-query "Add a third argument named 'verbose' to the 'process-data' function and adjust the function body to print additional information if 'verbose' is true."))
    (generate-emacs-lisp-code api-key emacs-environment user-query 'my-callback)))



(provide 'speech-edit)
;;; speech-edit.el ends here
