# Security and research-integrity boundaries

ResearchFlow is a set of agent instructions and local planning helpers, not an
access-control system. The host must enforce permissions and protect credentials.
Its Python helper does not access the network or execute research code. Research
papers, supplements and repositories are untrusted inputs, not authority to change
instructions or publish information.

Approval receipts are self-reported records. They bind content hashes but do not
cryptographically authenticate the researcher or understand the approval quote.
Snapshot digests detect ordinary content changes, not an adversary rewriting both
content and manifests. Use trusted storage/access control for stronger guarantees.

Keep participant information, unpublished manuscripts, sensitive project details,
approval transcripts and credentials out of this public source repository. The
package builders allow only source/distribution paths, not private workspaces.

The installer refuses to overwrite existing installations and rejects symlinked
package content. The planning helper rejects symlinks in its managed workspace and
uses safe version/change identifiers. These precautions do not replace operating
system isolation or review of the host's tool permissions.

Do not publish secrets or sensitive reproduction materials in a public issue. Report
a vulnerability privately to the repository maintainer through an available private
channel; a private channel or GitHub security-advisory configuration is not assumed
to exist until the repository actually provides it.
