FROM curlimages/curl:8.10.1

COPY forwarder.sh /usr/local/bin/suricata-alert-forwarder
USER root
RUN chmod +x /usr/local/bin/suricata-alert-forwarder
USER curl_user

ENTRYPOINT ["/usr/local/bin/suricata-alert-forwarder"]
