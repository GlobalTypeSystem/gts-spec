import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Nutanix AHV Virtual Machine Type
 *
 * GTS ID: gts.x.infra.vm.base.v1~nutanix.infra.vm.ahv.v1~
 *
 * Extends the base VM type with Nutanix AHV (Acropolis Hypervisor) specific properties.
 */
@jsonSchema("/schemas/gts.x.infra.vm.base.v1~nutanix.infra.vm.ahv.v1~.schema.json")
model NutanixAHVVM {
  /**
   * GTS identifier - must reference this derived type
   */
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.vm.base.v1~nutanix.infra.vm.ahv.v1~";

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
   * Nutanix-specific properties
   */
  nutanix: {
    /**
     * Nutanix VM UUID
     */
    vmUuid: string;

    /**
     * Cluster UUID where VM is running
     */
    clusterUuid: string;

    /**
     * Cluster name
     */
    clusterName: string;

    /**
     * Host UUID
     */
    hostUuid?: string;

    /**
     * Host name
     */
    hostName?: string;

    /**
     * Nutanix Guest Tools status
     */
    guestToolsStatus: "enabled" | "disabled" | "notInstalled";

    /**
     * Protection domain name (for disaster recovery)
     */
    protectionDomain?: string;

    /**
     * Categories assigned to the VM for grouping
     */
    categories?: Record<string>;

    /**
     * Storage container name
     */
    storageContainer?: string;

    /**
     * High availability priority
     */
    haPriority?: "high" | "medium" | "low";
  };

  /**
   * Additional metadata
   */
  metadata?: Record<string>;
}
