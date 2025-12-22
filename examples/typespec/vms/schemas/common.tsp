import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Common VM Metadata - strictly typed
 * 
 * Contains common metadata fields used across all VM types.
 * This model prevents arbitrary fields from being added - only
 * defined fields will pass validation.
 */
model VMMetadata {
  /**
   * Environment where the VM is deployed
   */
  environment?: "production" | "staging" | "development" | "test";

  /**
   * Owner or team responsible for the VM
   */
  owner?: string;

  /**
   * Cost center for billing purposes
   */
  costCenter?: string;

  /**
   * Project name or identifier
   */
  project?: string;

  /**
   * Backup schedule for the VM
   */
  backupSchedule?: "hourly" | "daily" | "weekly" | "monthly" | "none";
}

/**
 * Nutanix AHV-specific metadata - strictly typed
 */
model NutanixMetadata {
  /** Nutanix VM UUID */
  vmUuid: string;

  /** Nutanix cluster UUID */
  clusterUuid: string;

  /** Nutanix cluster name */
  clusterName: string;

  /** Host UUID where VM is running */
  hostUuid: string;

  /** Host name */
  hostName: string;

  /** Guest tools status */
  guestToolsStatus: "enabled" | "disabled" | "not_installed";

  /** Protection domain for backup/DR */
  protectionDomain?: string;

  /** Nutanix categories for organization */
  categories?: Record<string>;

  /** Storage container name */
  storageContainer: string;

  /** High availability priority */
  haPriority: "high" | "medium" | "low";

  /** Backup schedule */
  backupSchedule?: "hourly" | "daily" | "weekly" | "monthly" | "none";
}

/**
 * VMWare ESXi-specific metadata - strictly typed
 */
model VMWareMetadata {
  /** VMWare Managed Object Reference (MoRef) ID */
  moRefId: string;

  /** ESXi host name */
  hostName: string;

  /** Datacenter name in vCenter */
  datacenter: string;

  /** Cluster name */
  clusterName?: string;

  /** VMWare Tools status */
  guestToolsStatus: "running" | "notRunning" | "notInstalled" | "unknown";

  /** VMWare Tools version */
  guestToolsVersion?: string;

  /** Hardware version (e.g., vmx-19) */
  hardwareVersion: string;

  /** Resource pool assignment */
  resourcePool?: string;

  /** vMotion enabled flag */
  vMotionEnabled: boolean;

  /** Distributed Resource Scheduler mode */
  drsMode?: "fullyAutomated" | "partiallyAutomated" | "manual" | "disabled";

  /** Fault Tolerance enabled */
  ftEnabled?: boolean;

  /** Storage container name */
  storageContainer?: string;

  /** High availability priority */
  haPriority?: "high" | "medium" | "low";

  /** Backup schedule */
  backupSchedule?: "hourly" | "daily" | "weekly" | "monthly" | "none";
}

/**
 * Virtuozzo-specific metadata - strictly typed
 */
model VirtuozzoMetadata {
  /** Virtuozzo environment ID (VEID) */
  veid: string;

  /** Environment type */
  envType: "vm" | "container";

  /** Host node name */
  nodeName: string;

  /** Host node UUID */
  nodeUuid?: string;

  /** Template used to create the VM/CT */
  osTemplate: string;

  /** Virtuozzo Storage cluster name */
  storageCluster?: string;

  /** High availability enabled */
  haEnabled: boolean;

  /** CPU limit in MHz */
  cpuLimitMhz?: int32;

  /** CPU units (relative weight) */
  cpuUnits?: int32;

  /** Disk space limit in GB */
  diskSpaceGb?: int32;

  /** Backup node name for HA */
  backupNodeName?: string;

  /** License type */
  licenseType?: "perpetual" | "subscription" | "trial";

  /** Network type */
  networkType?: "bridged" | "routed" | "host-only";

  /** Backup schedule */
  backupSchedule?: "hourly" | "daily" | "weekly" | "monthly" | "none";
}
