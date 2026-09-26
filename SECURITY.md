# Security Policy

## Intended Use

This project is intended for local development or a trusted private Wi-Fi
network. It must not be exposed to the public internet or used as an open
proxy.

## Reporting a Vulnerability

Do not include credentials, private IP addresses, logs, or other personal data
in an issue. Before reporting, remove any local authentication files and test
artifacts from the report.

For sensitive reports, use GitHub's private vulnerability reporting feature when
it is enabled for the repository.

## Limitations

The Wi-Fi mode uses Basic proxy authentication. Basic authentication is not
encryption, so use it only on a trusted network and prefer HTTPS destinations.
This project is not an anonymity service or a replacement for a properly
secured VPN or production proxy.
