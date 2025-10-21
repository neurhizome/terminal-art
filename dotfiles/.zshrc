export LANG=en_US.UTF-8; export LC_ALL=en_US.UTF-8
autoload -Uz colors && colors
PROMPT='%{$fg[cyan]%}%n%{$reset_color%}@%{$fg[yellow]%}%m %{$fg[green]%}%~%{$reset_color%}%# '
