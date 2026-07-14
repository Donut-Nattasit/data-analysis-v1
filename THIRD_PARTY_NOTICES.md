# Third-party components

This repository's source files do not grant redistribution rights for separately
licensed tools, data, or assets.

## CEIC API client and data

The optional `ceic-api-client` wheel is proprietary and may be used only under the
legal conditions of the user's CEIC contract. The wheel and any downloaded CEIC
data are intentionally excluded from Git. Authorized users should place version
`2.11.5.396` in `wheels/` and rerun `setup.ps1`. Obtain it only through the
organization's CEIC administrator or another source authorized by the applicable
CEIC contract.

## FC Vision

FC Vision is a third-party commercial font whose embedded metadata prohibits
redistribution without written permission. Font binaries are intentionally excluded
from Git. Each authorized user must supply their own licensed files under
`.agents/skills/apply-nesdc-viz-template/assets/fonts/FCVision/`. Obtain them from
the organization's authorized brand, design, IT, or licensing contact; do not
download copies from unofficial font sites.

## X-13ARIMA-SEATS

The `x13as.exe` executable is intentionally excluded from Git. Obtain the current
Windows distribution from the U.S. Census Bureau and place the executable at
`bin/x13as.exe` before using the `x13-sa` skill.

## Other data sources

API access and downloaded data remain subject to the terms of their providers,
including BOT, IMF, EIA, World Bank, Thailand MOC, and S&P Global. Do not commit
licensed or confidential data to the repository.
