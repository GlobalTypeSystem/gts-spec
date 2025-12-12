import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Nutanix AHV Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~
 *
 * Extends the base VM type with Nutanix AHV (Acropolis Hypervisor) specific properties.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~.schema.json")
model NutanixAHVVM {
  /**
   * GTS identifier - must reference this derived type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~";

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
   * Platform-specific metadata (Nutanix AHV properties)
   * Contains: vmUuid, clusterUuid, clusterName, hostUuid, hostName,
   * guestToolsStatus, protectionDomain, categories, storageContainer, haPriority
   */
  metadata?: Record<unknown>;
}
