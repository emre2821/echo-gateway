"""
Eden Event Spine
Canonical neural vocabulary for cross-engine signaling.
No imports from engines. No side effects. Constants only.
"""

# === CHAOS (cognition) ===
CHAOS_FILE_CREATED   = "chaos.file.created"
CHAOS_FILE_UPDATED   = "chaos.file.updated"
CHAOS_FILE_DELETED   = "chaos.file.deleted"
CHAOS_ANALYZED       = "chaos.file.analyzed"
CHAOS_TAG_CREATED    = "chaos.tag.created"

# === CONTEXT (memory) ===
CONTEXT_ENTRY_ADDED  = "context.entry.added"
CONTEXT_MERGED       = "context.merged"
CONTEXT_CLEARED      = "context.cleared"

# === FILESYSTEM (embodiment) ===
FS_READ              = "filesystem.read"
FS_WRITTEN           = "filesystem.written"
FS_DELETED           = "filesystem.deleted"
FS_MOVED             = "filesystem.moved"
FS_MAPPED            = "filesystem.mapped"

# === MEDIA (senses) ===
MEDIA_REGISTERED     = "media.registered"
MEDIA_TAG_UPDATED    = "media.tag.updated"
MEDIA_DELETED        = "media.deleted"

# === PERMISSIONS / ETHICS ===
PERMISSION_GRANTED   = "permissions.granted"
PERMISSION_REVOKED   = "permissions.revoked"
PERMISSION_DENIED    = "permissions.denied"
AUDIT_EVENT          = "audit.event"

# === AGENT TRUST / GOVERNANCE ===
AGENT_REGISTERED     = "agent.registered"
AGENT_TRUST_CHANGED  = "agent.trust.changed"
AGENT_REVOKED        = "agent.revoked"
AGENT_ACCESSED       = "agent.accessed"

# === UTILITIES / OPERATIONS ===
ARCHIVE_CREATED      = "utility.archive.created"
CHECKSUM_CALCULATED  = "utility.checksum.calculated"
GIT_STATUS_QUERIED   = "utility.git.status"

# === BACKBONE / ECOSYSTEM ===
DCA_EVENT            = "backbone.dca.event"
AOE_EVENT            = "backbone.aoe.event"
CHAOS_BACKBONE_PING  = "backbone.chaos.ping"
EDEN_HEARTBEAT       = "backbone.eden.heartbeat"

# === SYSTEM ===
SYSTEM_STARTED       = "system.started"
SYSTEM_WARNING       = "system.warning"
SYSTEM_ERROR         = "system.error"
