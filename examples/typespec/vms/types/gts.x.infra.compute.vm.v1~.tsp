import "@typespec/json-schema";
import "./common.tsp";

using TypeSpec.JsonSchema;

/**
 * Base Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~
 *
 * This is the base type for all virtual machine definitions across
 * different virtualization platforms (VMWare, Nutanix, Virtuozzo, etc.).
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~.schema.json")
model BaseVM {
  /**
   * GTS identifier of the VM type
   */
  @extension("x-gts-ref", "/$id")
  type: string;

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
   * Number of virtual CPU cores allocated to the VM
   */
  @minValue(1)
  @maxValue(256)
  cpuCores: int32;

  /**
   * Amount of RAM in megabytes (MB)
   */
  @minValue(512)
  @maxValue(1048576)
  ramMb: int32;

  /**
   * Current power state of the virtual machine.
   * Reference to gts.x.infra.compute.vm_state.v1~ type.
   * See states/ directory for available state definitions.
   */
  @extension("x-gts-ref", "/gts.x.infra.compute.vm_state.v1~")
  powerState: string;

  /**
   * Operating system type running on the VM
   */
  osType?: string;

  /**
   * Timestamp when the VM was created
   */
  @format("date-time")
  createdAt: utcDateTime;

  /**
   * Environment where the VM is deployed.
   * Reference to gts.x.infra.env.v1~ for extensibility.
   */
  environment?: string;

  /**
   * Owner of the VM (team, user, or service account)
   */
  owner?: string;

  /**
   * Additional metadata (strictly typed)
   */
  metadata?: VMMetadata;
}
