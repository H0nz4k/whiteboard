alias camrestart="systemctl restart startcamera.service && systemctl status startcamera.service"
alias system-log="journalctl --follow"
alias whence="type -a"
alias ls="ls -lah --group-directories-first --color"

function cd() {
  command cd "$@" && ls -F --color=auto --show-control-chars --group-directories-first --color=auto
}
