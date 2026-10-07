FROM jenkins/jenkins:2.580.1-lts-jdk21

# Docker CLI only (a static binary copied from the pinned CLI image). It talks to the
# Docker-in-Docker sidecar over TLS; the host Docker socket is never mounted.
USER root
COPY --from=docker:29.8.1-cli /usr/local/bin/docker /usr/local/bin/docker
# buildx provides BuildKit and `docker build --progress`; without it the CLI falls back to the deprecated legacy builder.
COPY --from=docker:29.8.1-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx

# SonarScanner CLI, pinned and checked against its published SHA-256.
ARG SCANNER_VERSION=8.1.0.6389
ARG SCANNER_SHA256=ab76ab3c360025e9108be5b55be066f304a164f8b2850d2f2f333915db51bc1b
RUN curl -fsSL -o /tmp/scanner.zip \
      "https://repo1.maven.org/maven2/org/sonarsource/scanner/cli/sonar-scanner-cli/${SCANNER_VERSION}/sonar-scanner-cli-${SCANNER_VERSION}.zip" \
 && echo "${SCANNER_SHA256}  /tmp/scanner.zip" | sha256sum -c - \
 && mkdir -p /opt && cd /opt && jar xf /tmp/scanner.zip \
 && mv "/opt/sonar-scanner-${SCANNER_VERSION}" /opt/sonar-scanner \
 && chmod +x /opt/sonar-scanner/bin/* \
 && ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner \
 && rm /tmp/scanner.zip

# The seeded repository is owned by another user inside the shared volume.
RUN git config --system --add safe.directory '*'

USER jenkins
# ALLOW_LOCAL_CHECKOUT lets the Git plugin read the seeded repository from a local path (a read-only volume).
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true" \
    CASC_JENKINS_CONFIG=/usr/share/jenkins/casc

# Plugins pinned to exact versions and baked into the image.
COPY plugins.yaml /usr/share/jenkins/ref/plugins.yaml
RUN jenkins-plugin-cli --jenkins-version 2.568.3 --plugin-file /usr/share/jenkins/ref/plugins.yaml

# Jenkins Configuration as Code. It holds placeholders only; the values arrive as environment variables.
COPY casc/jenkins.yaml /usr/share/jenkins/casc/jenkins.yaml
