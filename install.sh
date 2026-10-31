#!/usr/bin/env bash
set -e
INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean_subscriptions.py"

mkdir -p "${INSTALL_DIR}"
cat << WRAPPEREOF > "${INSTALL_DIR}/gh-clean"
#!/usr/bin/env bash
python3 "${SCRIPT_SRC}" "\$@"
WRAPPEREOF

chmod +x "${INSTALL_DIR}/gh-clean"
chmod +x "${SCRIPT_SRC}"
echo "✅ gh-clean instalado en ${INSTALL_DIR}/gh-clean"
