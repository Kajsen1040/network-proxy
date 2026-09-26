# Local Proxy

`myproxy1.py` is a small HTTP forward proxy that uses only Python's standard
library. It forwards data and does not execute content returned by upstream
servers.

## Start Locally

From this folder, run:

```powershell
python myproxy1.py
```

The proxy listens on `127.0.0.1:8080`. To use another local port:

```powershell
python myproxy1.py --port 8888
```

For `curl`:

```powershell
curl.exe --proxy http://127.0.0.1:8080 http://example.com/
```

In a browser, set the HTTP and HTTPS proxy to `127.0.0.1` with port `8080`.

## Use As a Wi-Fi Proxy

Only use this mode on a trusted private Wi-Fi network. Create a local file
named `proxy-auth.txt` containing one line:

```text
proxyuser:choose-a-long-password
```

Start the proxy on the computer's Wi-Fi interface:

```powershell
python myproxy1.py --host 0.0.0.0 --port 8080 --auth-file .\proxy-auth.txt
```

Find the computer's private Wi-Fi address with `ipconfig`. Configure each
client device to use that address and port `8080` as its HTTP and HTTPS proxy.
Enter the username and password from `proxy-auth.txt` when prompted.

Allow inbound TCP port `8080` in the computer's firewall only for the trusted
private network. Do not port-forward this proxy from the router or expose it
to the public internet. Stop it with `Ctrl+C` when finished.

## Supported Requests

- `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS` requests
  for HTTP URLs
- HTTPS `CONNECT` tunnels to port `443`
- Hop-by-hop headers are removed before forwarding
- Invalid URLs, invalid ports, and credential-bearing URLs are rejected
- Client addresses and request lines are not logged
- Wi-Fi mode requires Basic proxy authentication

The proxy does not cache responses or inspect TLS traffic. Client request
bodies are limited to 10 MiB, and chunked client requests are not supported.

## Use Cases

- Learn how an HTTP forward proxy receives and forwards requests
- Test a local HTTP client or browser's proxy configuration
- Share a proxy with trusted devices on a private Wi-Fi network
- Experiment with headers using a controlled local service
- Provide a simple proxy for development tools that support proxies

## Privacy Expectations

This is a local privacy aid, not an anonymity service. It avoids adding proxy
request logs on this computer, and HTTPS `CONNECT` keeps HTTPS content
encrypted between the client and the destination. It does not hide the
computer's public IP address from websites, hide browsing metadata from the
internet provider, or remove cookies and browser fingerprints.

For destination-IP privacy, use a trusted remote proxy, VPN, or privacy network.
That service can observe your traffic, so use only a service you trust and
prefer HTTPS destinations. This program does not provide remote proxy
credentials or encryption to a remote proxy.

## Stop

Press `Ctrl+C` in the terminal running the proxy. The server exits and releases
its listening port. If the terminal is closed unexpectedly, verify that no
Python process is still running before starting another copy.

## Security Notes

- Keep the proxy bound to `127.0.0.1` unless Wi-Fi sharing is required.
- Wi-Fi mode requires `--auth-file` and firewall restrictions.
- Basic authentication is not encryption; use Wi-Fi mode only on a trusted
  network and prefer HTTPS destinations.
- Use HTTPS URLs for sensitive information.
- Do not expose the proxy to the public internet.
- Treat forwarded responses as untrusted data; the proxy only transports bytes.

## License

This project is available under the [MIT License](LICENSE).
