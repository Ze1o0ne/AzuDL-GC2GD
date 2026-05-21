# Security Features GUI Implementation

Complete code for the new "Security" tab in AzuDL-GC2GD GUI.

Add this method to the `AzuDlGC2GDGUI` class:

```python
def build_security_tab(self):
    """Build Security & Privacy Features Tab"""
    
    # Blocklists section
    self.blocklist_enable = self.checkbox("Enable IP blocklists", False, "260px")
    self.blocklist_types = widgets.SelectMultiple(
        description="Blocklists",
        options=[
            ("Level 1 - Anti-spyware & adware", "level1"),
            ("Level 2 - Malware & trojans", "level2"),
            ("Bad Peers - Malicious trackers", "badpeers")
        ],
        value=("level1", "badpeers"),
        layout=widgets.Layout(width="400px", height="100px")
    )
    
    enable_blocklist = self.button("Download & Enable", "success", "200px")
    enable_blocklist.on_click(self.handle_enable_blocklists)
    
    blocklist_status = self.button("Blocklist Status", "info", "160px")
    blocklist_status.on_click(self.handle_blocklist_status)
    
    clear_cache = self.button("Clear Cache", "warning", "140px")
    clear_cache.on_click(self.handle_clear_blocklist_cache)
    
    # File encryption section
    self.encryption_password = self.text("Encryption password", "Leave blank to auto-generate")
    self.verify_hash = self.checkbox("Verify checksums after download", True, "300px")
    self.hash_algorithm = widgets.Dropdown(
        description="Hash algo",
        options=[("SHA256", "sha256"), ("SHA512", "sha512"), ("BLAKE2b", "blake2b")],
        value="sha256",
        layout=widgets.Layout(width="260px"),
        style={"description_width": "90px"}
    )
    
    generate_key = self.button("Generate Key", "info", "145px")
    generate_key.on_click(self.handle_generate_encryption_key)
    
    # Security status
    security_status = self.button("Security Status", "info", "165px")
    security_status.on_click(self.handle_security_status)
    
    help_encryption = self.button("Encryption guide", "neutral", "160px")
    help_encryption.on_click(self.handle_encryption_help)
    
    help_privacy = self.button("Privacy guide", "neutral", "145px")
    help_privacy.on_click(self.handle_privacy_help)
    
    return self.panel(
        "Security & Privacy",
        "Enable IP blocklists, file encryption, and integrity verification for enhanced security.",
        [
            self.note("Enable blocklists to block malicious peers. File encryption adds an extra security layer before Drive upload."),
            
            # Blocklists section
            widgets.HTML(value="<div class='azudl-panel-title' style='margin-top:12px'>IP Blocklists</div>"),
            self.blocklist_types,
            self.action_row([enable_blocklist, blocklist_status, clear_cache]),
            
            # Encryption section
            widgets.HTML(value="<div class='azudl-panel-title' style='margin-top:16px'>File Encryption</div>"),
            self.encryption_password,
            self.action_row([generate_key]),
            
            # Verification section
            widgets.HTML(value="<div class='azudl-panel-title' style='margin-top:16px'>Integrity Verification</div>"),
            self.action_row([self.verify_hash, self.hash_algorithm]),
            
            # Status & Help
            self.action_row([security_status, help_encryption, help_privacy])
        ]
    )

# Add these handler methods to AzuDlGC2GDGUI class:

def handle_enable_blocklists(self, button):
    """Enable IP blocklists."""
    def action():
        self.app.enable_blocklists(download=True)
        self.app.log_security_event("blocklists_enabled", "User enabled IP blocklists")
    
    self.run_action(button, "Enable IP Blocklists", action)

def handle_blocklist_status(self, button):
    """Show blocklist cache status."""
    def action():
        self.app.print_section("IP Blocklist Status")
        cached = self.app.blocklist_manager.list_cached_blocklists()
        
        if not cached:
            self.app.print_status("No blocklists cached yet. Download them first.", "info")
            return
        
        self.app.print_subsection("Cached Blocklists")
        for key, info in cached.items():
            self.app.print_kv(key, f"{info['size']:,} bytes")
            self.app.print_kv("Updated", info['updated'])
            self.app.print_kv("Description", info['description'])
            print()
    
    self.run_action(button, "Blocklist Status", action)

def handle_clear_blocklist_cache(self, button):
    """Clear blocklist cache."""
    def action():
        self.app.blocklist_manager.clear_cache()
        self.app.log_security_event("blocklist_cache_cleared", "User cleared blocklist cache")
    
    self.run_action(button, "Clear Blocklist Cache", action)

def handle_generate_encryption_key(self, button):
    """Generate secure encryption key."""
    def action():
        password = self.app.generate_encryption_key()
        self.app.print_section("Encryption Key Generated")
        self.app.print_status("Key saved securely to: " + str(self.app.encryption_password_file), "success")
        self.encryption_password.value = password
        self.app.print_kv("Key", password)
        self.app.print_status("Save this key somewhere safe if you plan to decrypt files later!", "warning")
        self.app.log_security_event("encryption_key_generated", "New encryption key generated")
    
    self.run_action(button, "Generate Encryption Key", action)

def handle_security_status(self, button):
    """Show security status."""
    self.run_action(button, "Security & Privacy Status", self.app.print_security_status)

def handle_encryption_help(self, button):
    """Show encryption guide."""
    def action():
        self.app.print_section("File Encryption Guide", "Protect sensitive downloads with AES-128-CBC encryption")
        print("""
File Encryption Features:
- Algorithm: Fernet (AES-128-CBC)
- Key Derivation: PBKDF2 (100,000 iterations)
- Salt: 256-bit (cryptographically secure)
- Authentication: HMAC-SHA256

When to Use:
1. Sensitive torrents (private trackers)
2. Private files from GitHub
3. Confidential YouTube content
4. Protected backups

How It Works:
1. Generate a strong encryption key or provide your own password
2. Encrypt file locally before Drive upload
3. Original file securely deleted (optional)
4. Encrypted file stored on Drive with .encrypted extension
5. Decrypt with same key when needed

Security Best Practices:
- Store encryption keys separately from Drive
- Use strong, unique passwords (48+ characters)
- Never share encryption keys publicly
- Keep backup of decryption keys
- Verify file checksums before and after encryption

Encryption Key Storage Options:
1. Password Manager (LastPass, 1Password, Bitwarden)
2. Encrypted note (Apple Notes, Notion)
3. Paper backup in safe location
4. Hardware security key (YubiKey, Titan)

Never Store Keys:
✗ In Google Drive
✗ On GitHub
✗ In plaintext files
✗ In email

Example Workflow:
1. Download sensitive file via torrent
2. Encrypt: app.encrypt_download_before_drive(file)
3. Store password in 1Password
4. Upload encrypted file to Drive
5. Delete original from Colab
6. When needed: Decrypt with password
        """.strip())
    
    self.run_action(button, "Encryption Help", action)

def handle_privacy_help(self, button):
    """Show privacy best practices."""
    def action():
        self.app.print_section("Privacy & Security Best Practices", "Protect your downloads and identity")
        print("""
Privacy Enhancements in AzuDL:

1. TORRENT ENCRYPTION (ENFORCED):
   ✓ All torrent connections encrypted (arc4)
   ✓ Requires peer encryption capability
   ✓ Prevents ISP throttling detection
   ✓ Blocks plaintext peer connections

2. IP BLOCKLISTS (3 Free Sources):
   ✓ Level 1: Blocks spyware, adware, throttlers
   ✓ Level 2: Blocks malware, trojans, botnets
   ✓ BadPeers: Blocks malicious peers & honey pots
   ✓ ~7.5MB coverage, ~25,000+ IP ranges

3. PRIVATE MODE (For Private Trackers):
   ✓ Disables DHT (Distributed Hash Table)
   ✓ Disables PEX (Peer Exchange)
   ✓ Disables LPD (Local Peer Discovery)
   ✓ Prevents IP leaks to tracker networks

4. FILE ENCRYPTION:
   ✓ AES-128-CBC with PBKDF2 key derivation
   ✓ 256-bit random salt
   ✓ HMAC-SHA256 authentication
   ✓ Optionally encrypt before Drive upload

5. NETWORK PRIVACY:
   ✓ RPC secret protects local communication (48 bytes)
   ✓ Limited peer connections (max 100)
   ✓ Custom peer ID (AzuDL - no identifying software)
   ✓ No user-agent leakage
   ✓ Peer speed limiting (50K throttle)

6. INTEGRITY VERIFICATION:
   ✓ SHA256, SHA512, BLAKE2b checksums
   ✓ Verify torrent infohash before adding
   ✓ Secure download manifests
   ✓ Detect tampering or corruption

7. CREDENTIAL SECURITY:
   ✓ File permissions: 0o600 (owner only)
   ✓ Encrypted storage for sensitive tokens
   ✓ No credentials in logs
   ✓ Masked URLs in error messages

Responsible Use Guidelines:
- Only download content you own or have permission for
- Respect torrent tracker rules and terms
- Follow copyright laws in your jurisdiction
- Use private mode for private tracker content
- Never share encryption keys publicly
- Never upload real credentials to GitHub
- Keep authentication files private

Privacy Levels:

PUBLIC TORRENTS (Recommended: Enable blocklists):
1. Enable IP blocklists
2. Use standard torrent mode
3. Monitor bandwidth
4. Optional: Encrypt before Drive

PRIVATE TRACKERS (Recommended: Private mode + encryption):
1. Enable private mode
2. Enable IP blocklists
3. Encrypt sensitive content
4. Use VPN (optional, for extra privacy)

HIGHLY SENSITIVE (Recommended: All protections):
1. Enable private mode
2. Enable IP blocklists
3. Enable file encryption
4. Use VPN with proxy support
5. Verify all checksums
6. Use unique encryption key

For More Information:
- See SECURITY_AUDIT.md for technical details
- See IMPLEMENTATION_GUIDE.md for setup instructions
        """.strip())
    
    self.run_action(button, "Privacy Guide", action)
```

## Integration in Main Build Method

Update the `build()` method in `AzuDlGC2GDGUI`:

```python
def build(self):
    header = widgets.HTML(value=f"""
    <div class="azudl-hero">
      <div class="azudl-title">{self.app.project_name}</div>
      <div class="azudl-subtitle">Universal downloader for Google Colab with Google Drive storage</div>
      <span class="azudl-badge">Version {self.app.version}</span>
    </div>
    """)

    tabs = widgets.Tab(children=[
        self.build_dashboard_tab(),
        self.build_auto_tab(),
        self.build_direct_tab(),
        self.build_youtube_tab(),
        self.build_auth_tab(),
        self.build_torrent_tab(),
        self.build_batch_tab(),
        self.build_github_tab(),
        self.build_official_project_tab(),
        self.build_files_tab(),
        self.build_archives_tab(),
        self.build_security_tab(),      # NEW: Security tab
        self.build_maintenance_tab(),
        self.build_developer_tab(),
        self.build_guide_tab()
    ])
    tabs.add_class("azudl-tabs")

    titles = [
        "Dashboard",
        "Auto",
        "Direct",
        "YouTube",
        "Auth",
        "Torrent",
        "Batch",
        "GitHub",
        "Official",
        "Files",
        "Archives",
        "Security",  # NEW: Security tab title
        "Maintenance",
        "Developer",
        "Guide"
    ]

    for index, title in enumerate(titles):
        tabs.set_title(index, title)

    # ... rest of build method remains the same ...
```

## CSS Styling (Already Included)

The security tab automatically inherits all existing CSS styling:
- `.azudl-button` - Buttons
- `.azudl-panel` - Panel containers
- `.azudl-note` - Info notes
- `.azudl-action-row` - Horizontal button layout

No additional CSS needed - uses existing theme!
