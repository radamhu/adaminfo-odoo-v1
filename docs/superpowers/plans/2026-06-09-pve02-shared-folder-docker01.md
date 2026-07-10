# pve02 → docker01 Shared Folder Mount Plan (VirtIO-FS)

> **Infrastructure plan — requires manual execution via SSH on pve02 and docker01.**

**Goal:** Mount `/media/ssd/shared01` from pve02 Proxmox host into docker01 VM via VirtIO-FS so all running Docker containers (torrent, emby, samba) have read-write access.

**Architecture:** VirtIO-FS (virtiofsd) share configured on pve02 → single planned VM restart of docker01 → virtiofs mount in the guest → bind-mount path added to each container one at a time. No NFS daemon, no network protocol overhead — near-native filesystem performance via shared memory.

**Tech Stack:** Proxmox 8.x qemu-server (includes virtiofsd), virtiofs kernel module (included in modern Linux kernels), docker-compose or docker run volume flags

---

## Pre-Flight: Gather Facts

- [ ] **Step 1: Get docker01's VMID**

  ```bash
  ssh root@192.168.0.11
  qm list
  ```
  Note the VMID (e.g. `100`). Used as `<VMID>` throughout this plan.

- [ ] **Step 2: Identify how each container is managed**

  ```bash
  ssh root@$(qm guest cmd <VMID> network-get-interfaces 2>/dev/null | \
    grep -oP '(?<="ip-address": ")[^"]+' | grep -v ':' | head -1)
  # or just SSH into docker01 directly if you know its IP
  find / -name "docker-compose.yml" -o -name "docker-compose.yaml" 2>/dev/null | head -20
  docker ps --format 'table {{.Names}}\t{{.Image}}'
  ```
  Note whether containers are managed by **docker-compose** or bare **docker run**.

- [ ] **Step 3: Capture current volume mounts for each container**

  ```bash
  docker inspect torrent | grep -A20 '"Mounts"'
  docker inspect emby    | grep -A20 '"Mounts"'
  docker inspect samba   | grep -A20 '"Mounts"'
  ```
  Save this output — you need it when recreating containers in Task 3.

---

## Task 1: Add VirtIO-FS Share on pve02

**Files modified on pve02:**
- `/etc/pve/qemu-server/<VMID>.conf`

- [ ] **Step 1: Verify virtiofsd is available**

  ```bash
  ssh root@192.168.0.11
  which virtiofsd || dpkg -l | grep virtiofsd
  ```
  Expected: a path or package line. If missing: `apt-get install -y virtiofsd`

- [ ] **Step 2: Check the folder exists and set permissions**

  ```bash
  ls -la /media/ssd/shared01
  chmod 0755 /media/ssd/shared01
  ```

- [ ] **Step 3: Add the share to the VM config**

  **Option A — Proxmox GUI (recommended):**
  - Open Proxmox web UI → docker01 VM → Hardware → Add → Directory Share
  - Set Path: `/media/ssd/shared01`, Tag: `shared01`
  - Click Add

  **Option B — CLI:**
  ```bash
  # Append to VM config (replace 100 with actual VMID)
  echo 'virtiofs0: /media/ssd/shared01' >> /etc/pve/qemu-server/<VMID>.conf
  # Verify
  grep virtiofs /etc/pve/qemu-server/<VMID>.conf
  ```
  Expected: `virtiofs0: /media/ssd/shared01`

- [ ] **Step 4: Restart docker01**

  ```bash
  qm reboot <VMID>
  ```
  Wait ~20–30 seconds, then confirm VM is back:
  ```bash
  qm status <VMID>
  ```
  Expected: `status: running`

---

## Task 2: Mount VirtIO-FS in docker01

**Files modified on docker01:**
- `/etc/fstab`

- [ ] **Step 1: SSH back into docker01 after reboot**

  ```bash
  ssh root@<DOCKER01_IP>
  ```

- [ ] **Step 2: Verify the virtiofs device is visible**

  ```bash
  ls /sys/bus/virtio/drivers/virtiofs/
  # or
  dmesg | grep virtiofs
  ```
  Expected: at least one entry confirming the virtiofs driver registered the share.

- [ ] **Step 3: Create mount point**

  ```bash
  mkdir -p /mnt/shared01
  ```

- [ ] **Step 4: Test manual mount**

  The mount tag matches the key name in the VM config (`virtiofs0`) unless you set a custom tag in the GUI (then use that tag):
  ```bash
  mount -t virtiofs virtiofs0 /mnt/shared01
  df -h /mnt/shared01
  ```
  Expected: shows the SSD capacity.

- [ ] **Step 5: Verify write access**

  ```bash
  touch /mnt/shared01/.write-test && rm /mnt/shared01/.write-test
  echo "Write test passed"
  ```

- [ ] **Step 6: Make persistent in /etc/fstab**

  ```bash
  umount /mnt/shared01
  ```
  Append to `/etc/fstab`:
  ```
  virtiofs0  /mnt/shared01  virtiofs  defaults  0  0
  ```

- [ ] **Step 7: Mount via fstab and verify**

  ```bash
  mount -a
  df -h /mnt/shared01
  touch /mnt/shared01/.write-test && rm /mnt/shared01/.write-test
  echo "Persistent mount OK"
  ```

---

## Task 3: Add Volume Mount to Each Container

> Repeat for **torrent**, then **emby**, then **samba** — one at a time.
> Each takes ~10–30 seconds of container downtime.

### Option A — docker-compose managed

- [ ] **Step 1: Edit the compose file for the container**

  Add under `volumes:` for the relevant service:
  ```yaml
  volumes:
    - /mnt/shared01:/shared
    # keep all existing volume entries
  ```

- [ ] **Step 2: Recreate only that service**

  ```bash
  docker compose up -d --no-deps <service-name>
  ```

- [ ] **Step 3: Verify write inside the container**

  ```bash
  docker exec <container-name> touch /shared/.write-test && \
    docker exec <container-name> rm /shared/.write-test
  echo "<container> write OK"
  ```

### Option B — bare docker run

- [ ] **Step 1: Stop and remove the container**

  ```bash
  docker stop <container-name>
  docker rm <container-name>
  ```

- [ ] **Step 2: Re-run with additional volume flag**

  Take the original run command (from Pre-Flight Step 3) and add `-v /mnt/shared01:/shared`:
  ```bash
  docker run -d \
    --name <container-name> \
    -v /existing/volume:/existing/path \
    -v /mnt/shared01:/shared \
    [all other original flags] \
    <image-name>
  ```

- [ ] **Step 3: Verify write inside the container**

  ```bash
  docker exec <container-name> touch /shared/.write-test && \
    docker exec <container-name> rm /shared/.write-test
  echo "<container> write OK"
  ```

---

## Task 4: Samba — Expose the New Share (if needed)

Only needed if the samba container should also *serve* this path over the network.

- [ ] **Step 1: Locate samba config on the host**

  ```bash
  docker inspect samba | grep -A5 '"Mounts"'
  # Find the host path mapped to the samba config directory
  ```

- [ ] **Step 2: Add a share block to smb.conf**

  ```ini
  [shared01]
     path = /shared
     browseable = yes
     writable = yes
     valid users = <your samba users>
  ```

- [ ] **Step 3: Reload samba config**

  ```bash
  docker exec samba smbcontrol all reload-config 2>/dev/null || docker restart samba
  ```

---

## Task 5: Smoke Test All Three Containers

- [ ] **Step 1: Write from each container, verify on pve02**

  On docker01:
  ```bash
  docker exec torrent sh -c 'echo torrent > /shared/.torrent-test'
  docker exec emby    sh -c 'echo emby    > /shared/.emby-test'
  docker exec samba   sh -c 'echo samba   > /shared/.samba-test'
  ```

  On pve02:
  ```bash
  ls -la /media/ssd/shared01/.*-test
  ```
  Expected: all three files present.

- [ ] **Step 2: Write from pve02, verify in all containers**

  On pve02:
  ```bash
  echo pve02 > /media/ssd/shared01/.pve02-test
  ```

  On docker01:
  ```bash
  docker exec torrent cat /shared/.pve02-test
  docker exec emby    cat /shared/.pve02-test
  docker exec samba   cat /shared/.pve02-test
  ```
  Expected: all three print `pve02`.

- [ ] **Step 3: Cleanup test files**

  On pve02:
  ```bash
  rm /media/ssd/shared01/.*-test
  ```

- [ ] **Step 4: Test reboot persistence**

  ```bash
  ssh root@<DOCKER01_IP> reboot
  # wait ~30s
  ssh root@<DOCKER01_IP> 'df -h /mnt/shared01 && docker exec torrent ls /shared'
  ```
  Expected: mount is back automatically, container can see the share.
