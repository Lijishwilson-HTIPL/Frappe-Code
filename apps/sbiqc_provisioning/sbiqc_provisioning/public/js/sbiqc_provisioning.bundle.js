import { createApp } from "vue";
import SBIQProvisioning from "./SBIQProvisioning.vue";

frappe.provide("sbiqc");
window.SBIQCProvisioning = SBIQProvisioning;

frappe.pages["sbiqc-provisioning"] = frappe.pages["sbiqc-provisioning"] || {};

frappe.pages["sbiqc-provisioning"].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: "SBIQ Provisioning",
        single_column: true,
    });
    $(wrapper).find(".page-head").addClass("hide");
    const mountEl = $(wrapper).find(".layout-main-section")[0];
    const app = createApp(SBIQProvisioning);
    app.mount(mountEl);
    wrapper.__sbiqc_vue = app;
};

frappe.pages["sbiqc-provisioning"].on_page_show = function (wrapper) {
    // Vue component handles its own refresh on mount/show via reactive state
};

frappe.pages["sbiqc-provisioning"].on_page_unload = function (wrapper) {
    if (wrapper.__sbiqc_vue) {
        wrapper.__sbiqc_vue.unmount();
        wrapper.__sbiqc_vue = null;
    }
};
