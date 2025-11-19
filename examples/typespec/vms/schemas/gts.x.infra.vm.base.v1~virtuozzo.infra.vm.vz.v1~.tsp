import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Virtuozzo Virtual Machine Type
 *
 * GTS ID: gts.x.infra.vm.base.v1~virtuozzo.infra.vm.vz.v1~
 *
 * Extends the base VM type with Virtuozzo-specific properties.
 * Virtuozzo supports both VMs and containers on the same platform.
 */
@jsonSchema("/schemas/gts.x.infra.vm.base.v1~virtuozzo.infra.vm.vz.v1~.schema.json")
model VirtuozzoVM {
  /**
   * GTS identifier - must reference this derived type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.vm.base.v1~virtuozzo.infra.vm.vz.v1~";

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
   * Virtuozzo-specific properties
   */
  virtuozzo: {
    /**
     * Virtuozzo environment ID (VEID)
     */
    veid: string;

    /**
     * Environment type
     */
    envType: "vm" | "container";

    /**
     * Host node name
     */
    nodeName: string;

    /**
     * Host node UUID
     */
    nodeUuid?: string;

    /**
     * Template used to create the VM/CT
     */
    osTemplate: string;

    /**
     * Virtuozzo Storage cluster name
     */
    storageCluster?: string;

    /**
     * High availability enabled
     */
    haEnabled: boolean;

    /**
     * CPU limit in MHz
     */
    cpuLimitMhz?: int32;

    /**
     * CPU units (relative weight)
     */
    cpuUnits?: int32;

    /**
     * Disk space limit in GB
     */
    diskSpaceGb?: int32;

    /**
     * Backup node name for HA
     */
    backupNodeName?: string;
  };

  /**
   * Additional metadata
   */
  metadata?: Record<string>;
}
