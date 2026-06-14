{ pkgs, ... }: {
  languages.python = {
    enable = true;
    package = pkgs.python311;
    venv = {
      enable = true;
      requirements = ./requirements-dev.txt;
    };
  };

  packages = [
    pkgs.python3Packages.ruff
    pkgs.python3Packages.black
  ];

  enterShell = ''
    echo "LaTeX to Python Translator - Dev Environment"
  '';
}
