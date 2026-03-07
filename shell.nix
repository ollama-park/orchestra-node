{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell rec {
  buildInputs = with pkgs; [
    (pkgs.python3.withPackages (ps: with ps; [
      grpcio
      grpcio-tools
      fastapi
      uvicorn
    ]))
  ];
}
