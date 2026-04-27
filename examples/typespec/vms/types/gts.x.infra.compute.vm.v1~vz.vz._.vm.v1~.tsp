import "@typespec/json-schema";
import "./common.tsp";

using TypeSpec.JsonSchema;

/**
 * Virtuozzo Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~
 *
 * Extends the base VM type with Virtuozzo properties.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~.schema.json")
model VirtuozzoVM {
  @extension("x-gts-ref", "/$id")
  type: "gts.x.infra.compute.vm.v1~vz.vz._.vm.v1~";

  @format("uuid")
  id: string;

  @minLength(1)
  @maxLength(255)
  name: string;

  @minValue(1)
  @maxValue(256)
  cpuCores: int32;

  @minValue(512)
  @maxValue(1048576)
  ramMb: int32;

  /** Reference to gts.x.infra.compute.vm_state.v1~ */
  @extension("x-gts-ref", "/gts.x.infra.compute.vm_state.v1~")
  powerState: string;

  osType?: string;

  @format("date-time")
  createdAt: utcDateTime;

  environment?: string;
  owner?: string;

  /** Virtuozzo-specific metadata (strictly typed) */
  metadata?: VirtuozzoMetadata;
}
