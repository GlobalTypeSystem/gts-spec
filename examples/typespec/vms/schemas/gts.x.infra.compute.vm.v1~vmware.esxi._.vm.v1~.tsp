import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * VMWare ESXi Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~
 *
 * Extends the base VM type with VMWare ESXi-specific properties.
 * This type inherits all base properties and adds VMWare-specific fields.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~.schema.json")
model VMWareESXiVM {
  /**
   * GTS identifier - must reference this derived type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.compute.vm.v1~vmware.esxi._.vm.v1~";

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
   * Power state
   */
  powerState: "running" | "stopped" | "suspended" | "paused";

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
   * Platform-specific metadata (VMWare ESXi properties)
   * Contains: moRefId, hostName, datacenter, cluster, toolsStatus,
   * toolsVersion, hardwareVersion, resourcePool, vMotionEnabled
   */
  metadata?: Record<unknown>;
}
