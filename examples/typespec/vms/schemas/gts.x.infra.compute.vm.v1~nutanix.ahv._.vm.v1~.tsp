import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Nutanix AHV Virtual Machine Type
 *
 * GTS ID: gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~
 *
 * Extends the base VM type with Nutanix AHV specific properties.
 */
@jsonSchema("/schemas/gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~.schema.json")
model NutanixAHVVM {
  @jsonSchema({ "x-gts-ref": "/$id" })
  gtsId: "gts.x.infra.compute.vm.v1~nutanix.ahv._.vm.v1~";

  @format("uuid")
  id: string;

  @minLength(1)
  @maxLength(255)
  name: string;

  @minimum(1)
  @maximum(256)
  cpuCores: int32;

  @minimum(512)
  @maximum(1048576)
  ramMb: int32;

  /** Reference to gts.x.infra.compute.vm_state.v1~ */
  @jsonSchema({ "x-gts-ref": "/gts.x.infra.compute.vm_state.v1~" })
  powerState: string;

  osType?: string;

  @format("date-time")
  createdAt: utcDateTime;

  environment?: string;
  owner?: string;
  metadata?: Record<unknown>;
}
