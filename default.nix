{pkgs ? import <nixpkgs> {}}:
with pkgs.pythonPackages;
buildPythonPackage {
  name = "pytest-boxed";
  src = ./.;
  buildInputs = [pytest setuptools_scm];
}