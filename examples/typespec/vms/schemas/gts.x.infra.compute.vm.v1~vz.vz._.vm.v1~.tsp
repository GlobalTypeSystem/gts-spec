import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Virtuozzo Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~
 *
 * Extends the base VM type with Virtuozzo-specific properties.
 * Virtuozzo supports both VMs and containers on the same platform.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~.schema.json")
model VirtuozzoVM {
  /**
   * GTS identifier - must reference this derived type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~";

  /**
   * Unique identifier of the VM instance
   */
  @format("uuid")
  id: string;

  /**
   * Human-readable name of the virtual machine
   */
  @minLength(1)
  @maxLength(255)
  name: string;

  /**
   * Number of virtual CPU cores
   */
  @minimum(1)
  @maximum(256)
  cpuCores: int32;

  /**
   * Amount of RAM in megabytes
   */
  @minimum(512)
  @maximum(1048576)
  ramMb: int32;

  /**
   * Power state with transient states
   */
  powerState: "running" | "stopped" | "suspended" | "paused" | "starting" | "stopping" | "suspending" | "rebooting" | "migrating";

  /**
   * Operating system type
   */
  osType?: string;

  /**
   * Creation timestamp
   */
  @format("date-time")
  createdAt: utcDateTime;

  /**
   * Environment where the VM is deployed
   */
  environment?: string;

  /**
   * Owner of the VM
   */
  owner?: string;

  /**
   * Platform-specific metadata (Virtuozzo properties)
   * Contains: veid, envType, nodeName, nodeUuid, osTemplate,
   * storageCluster, haEnabled, cpuLimitMhz, cpuUnits, diskSpaceGb, backupNodeName
   */
  metadata?: Record<unknown>;
}
