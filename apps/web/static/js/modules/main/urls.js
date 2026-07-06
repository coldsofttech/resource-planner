"use strict";

const API_BASE = "/api/v1/";

export const UI_URLS = {
  auth: {
    login: () => "/login/",
    forgotPassword: () => "/forgot-password/",
    register: () => "/register/",
    forceChangePassword: () => "/change-password-required/",
  },
  setup: {
    wizard: () => "/setup/",
  },
  teams: {
    list: () => "/teams/",
    detail: (code) => `/teams/${code}/`,
  },
  skills: {
    list: () => "/skills/",
    detail: (code) => `/skills/${code}/`,
  },
  roles: {
    list: () => "/roles/",
    detail: (code) => `/roles/${code}/`,
  },
  locations: {
    list: () => "/locations/",
    detail: (code) => `/locations/${code}/`,
  },
  empTypes: {
    list: () => "/emp-types/",
    detail: (code) => `/emp-types/${code}/`,
  },
  holidays: {
    list: () => "/holidays/",
  },
  leaves: {
    list: () => "/leaves/",
  },
  members: {
    list: () => "/members/",
  },
  users: {
    list: () => "/users/",
    detail: (code) => `/users/${code}/`,
  },
  groups: {
    list: () => "/groups/",
    detail: (code) => `/groups/${code}/`,
  },
  fy: {
    list: () => "/fy/",
  },
  reports: {
    standardList: () => "/reports/standard/",
    standardWeeklyWins: () => "/reports/standard/weekly-wins/",
    standardMonthlyWins: () => "/reports/standard/monthly-wins/",
    standardSprintForecastVsActuals: () => "/reports/standard/sprint-forecast-vs-actuals/",
    standardDemandVsCapacity: () => "/reports/standard/demand-vs-capacity/",
    standardDemandVsCapacityConfig: () => "/reports/standard/demand-vs-capacity/config/",
    standardKpiEstimateAccuracy: () => "/reports/standard/kpi-estimate-accuracy/",
    standardKpiEstimateAccuracyConfig: () => "/reports/standard/kpi-estimate-accuracy/config/",
    standardMonthlyFinanceReport: () => "/reports/standard/monthly-finance-report/",
    customList: () => "/reports/custom/",
    customBuilder: (code) => `/reports/custom/${code}/`,
  },
  sprints: {
    list: () => "/sprints/",
    detail: (code) => `/sprints/${code}/`,
    forecast: (code) => `/sprints/${code}/forecast/`,
    forecastImportDetail: (sprintCode, importCode) =>
      `/sprints/${sprintCode}/forecast/${importCode}/`,
    actuals: (code) => `/sprints/${code}/actuals/`,
    actualsImportDetail: (sprintCode, importCode) =>
      `/sprints/${sprintCode}/actuals/${importCode}/`,
  },
  programmes: {
    list: () => "/programmes/",
  },
  businessUnits: {
    list: () => "/bu/",
    detail: (code) => `/bu/${code}/`,
  },
  onboarding: {
    portal: () => "/onboarding/",
    review: () => "/demands/",
    create: () => "/demands/new/",
  },
  products: {
    list: () => "/products/",
  },
  projectSizes: {
    list: () => "/projects/sizes/",
  },
  projectTypes: {
    list: () => "/projects/types/",
  },
  recharges: {
    index: () => "/recharges/",
    detail: (code) => `/recharges/${code}/`,
    types: () => "/recharges/types/",
    typeDetail: (code) => `/recharges/types/${code}/`,
    projectGroups: () => "/recharges/project-groups/",
    emailReviewForecasts: (sprintCode) => `/recharges/${sprintCode}/forecasts/`,
    emailReviewActuals: (sprintCode) => `/recharges/${sprintCode}/actuals/`,
  },
  projectStatuses: {
    list: () => "/projects/statuses/",
  },
  projects: {
    list: () => "/projects/",
    detail: (code) => `/projects/${code}/`,
  },
  wins: {
    list: () => "/wins/",
    detail: (code) => `/wins/${code}/`,
    monthlyList: () => "/wins/monthly/",
    monthlyDetail: (code) => `/wins/monthly/${code}/`,
    monthlySurvey: (token) => `/wins/monthly/survey/${token}/`,
  },
  winsConfig: {
    page: () => "/wins/config/",
  },
  aiConfig: {
    page: () => "/configurations/ai/",
  },
  securityConfig: {
    page: () => "/configurations/security/",
  },
  notifications: {
    list: () => "/notifications/",
    preferences: () => "/notifications/preferences/",
  },
  toDo: {
    list: () => "/to-do/",
    preferences: () => "/to-do/preferences/",
  },
  resourcePlans: {
    list: () => "/resource-plans/",
    detail: (code) => `/resource-plans/${code}/`,
    versionDetail: (code, version) => `/resource-plans/${code}/versions/v${version}/`,
    versionGrid: (code, version) => `/resource-plans/${code}/versions/v${version}/grid/`,
    versionConflicts: (code, version) => `/resource-plans/${code}/versions/v${version}/conflicts/`,
    versionPlaceholderLeaves: (code, version) =>
      `/resource-plans/${code}/versions/v${version}/placeholder-leaves/`,
    versionUtilisation: (code, version) =>
      `/resource-plans/${code}/versions/v${version}/utilisation/`,
    versionSnapshots: (code, version) => `/resource-plans/${code}/versions/v${version}/snapshots/`,
    versionSnapshotAllocations: (code, version, snapshotCode) =>
      `/resource-plans/${code}/versions/v${version}/snapshots/${snapshotCode}/allocations/`,
  },
};

export const API_URLS = {
  meta: {
    get: () => ({ method: "GET", href: `${API_BASE}meta/` }),
  },
  auth: {
    login: () => ({ method: "POST", href: `${API_BASE}auth/login/` }),
    register: () => ({ method: "POST", href: `${API_BASE}auth/register/` }),
    forgotPassword: {
      request: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/` }),
      verify: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/verify/` }),
      reset: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/reset/` }),
    },
    oauth: {
      create: () => ({ method: "POST", href: `${API_BASE}auth/oauth/` }),
      authorize: (providerCode) => ({
        method: "GET",
        href: `${API_BASE}auth/oauth/${providerCode}/authorize/`,
      }),
      callback: () => ({ method: "POST", href: `${API_BASE}auth/oauth/callback/` }),
    },
    saml: {
      create: () => ({ method: "POST", href: `${API_BASE}auth/saml/` }),
      authorize: (providerCode) => ({
        method: "GET",
        href: `${API_BASE}auth/saml/${providerCode}/authorize/`,
      }),
    },
    logout: () => ({ method: "POST", href: `${API_BASE}auth/logout/` }),
    me: () => ({ method: "GET", href: `${API_BASE}auth/me/` }),
    forceChangePassword: () => ({
      method: "POST",
      href: `${API_BASE}auth/force-change-password/`,
    }),
  },
  users: {
    me: () => ({ method: "GET", href: `${API_BASE}users/me/` }),
    updatePreferences: () => ({ method: "PATCH", href: `${API_BASE}users/me/preferences/` }),
    updateProfile: () => ({ method: "PATCH", href: `${API_BASE}users/me/profile/` }),
    changePassword: () => ({ method: "POST", href: `${API_BASE}users/me/password/` }),
    avatar: () => ({ method: "GET", href: `${API_BASE}users/me/avatar/` }),
    uploadAvatar: () => ({ method: "POST", href: `${API_BASE}users/me/avatar/upload/` }),
    options: () => ({ method: "GET", href: `${API_BASE}users/options/` }),
    setPassword: () => ({ method: "POST", href: `${API_BASE}auth/set-password/` }),
    adminList: () => ({ method: "GET", href: `${API_BASE}users/` }),
    adminCreate: () => ({ method: "POST", href: `${API_BASE}users/` }),
    adminStats: () => ({ method: "GET", href: `${API_BASE}users/stats/` }),
    adminDetail: (code) => ({ method: "GET", href: `${API_BASE}users/${code}/` }),
    adminDelete: (code) => ({ method: "DELETE", href: `${API_BASE}users/${code}/` }),
    adminActivate: (code) => ({ method: "POST", href: `${API_BASE}users/${code}/activate/` }),
    adminDeactivate: (code) => ({ method: "POST", href: `${API_BASE}users/${code}/deactivate/` }),
    adminResetPassword: (code) => ({
      method: "POST",
      href: `${API_BASE}users/${code}/reset-password/`,
    }),
    adminExportSpecs: () => ({ method: "GET", href: `${API_BASE}users/export/specs/` }),
    adminExport: () => ({ method: "GET", href: `${API_BASE}users/export/` }),
    search: (q) => ({
      method: "GET",
      href: `${API_BASE}users/search/?q=${encodeURIComponent(q || "")}`,
    }),
  },
  teams: {
    list: () => ({ method: "GET", href: `${API_BASE}teams/` }),
    create: () => ({ method: "POST", href: `${API_BASE}teams/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}teams/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}teams/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}teams/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}teams/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}teams/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}teams/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}teams/${code}/deactivate/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}teams/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}teams/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}teams/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}teams/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}teams/export/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}teams/${code}/members/` }),
  },
  skills: {
    list: () => ({ method: "GET", href: `${API_BASE}skills/` }),
    options: () => ({ method: "GET", href: `${API_BASE}skills/options/` }),
    create: () => ({ method: "POST", href: `${API_BASE}skills/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}skills/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}skills/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}skills/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}skills/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}skills/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}skills/${code}/deactivate/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}skills/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}skills/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}skills/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}skills/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}skills/export/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}skills/${code}/members/` }),
  },
  roles: {
    list: () => ({ method: "GET", href: `${API_BASE}roles/` }),
    options: () => ({ method: "GET", href: `${API_BASE}roles/options/` }),
    create: () => ({ method: "POST", href: `${API_BASE}roles/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}roles/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}roles/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}roles/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}roles/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}roles/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}roles/${code}/deactivate/` }),
    setDefault: (code) => ({ method: "POST", href: `${API_BASE}roles/${code}/set-default/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}roles/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}roles/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}roles/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}roles/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}roles/export/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}roles/${code}/members/` }),
  },
  locations: {
    list: () => ({ method: "GET", href: `${API_BASE}locations/` }),
    options: () => ({ method: "GET", href: `${API_BASE}locations/options/` }),
    create: () => ({ method: "POST", href: `${API_BASE}locations/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}locations/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}locations/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}locations/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}locations/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}locations/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}locations/${code}/deactivate/` }),
    setDefault: (code) => ({ method: "POST", href: `${API_BASE}locations/${code}/set-default/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}locations/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}locations/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}locations/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}locations/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}locations/export/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}locations/${code}/members/` }),
  },
  empTypes: {
    list: () => ({ method: "GET", href: `${API_BASE}emp-types/` }),
    options: () => ({ method: "GET", href: `${API_BASE}emp-types/options/` }),
    create: () => ({ method: "POST", href: `${API_BASE}emp-types/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}emp-types/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}emp-types/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}emp-types/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}emp-types/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}emp-types/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}emp-types/${code}/deactivate/` }),
    setDefault: (code) => ({ method: "POST", href: `${API_BASE}emp-types/${code}/set-default/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}emp-types/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}emp-types/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}emp-types/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}emp-types/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}emp-types/export/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}emp-types/${code}/members/` }),
  },
  holidays: {
    list: () => ({ method: "GET", href: `${API_BASE}holidays/` }),
    options: () => ({ method: "GET", href: `${API_BASE}holidays/options/` }),
    create: () => ({ method: "POST", href: `${API_BASE}holidays/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}holidays/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}holidays/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}holidays/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}holidays/${code}/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}holidays/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}holidays/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}holidays/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}holidays/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}holidays/export/` }),
  },
  leaves: {
    list: () => ({ method: "GET", href: `${API_BASE}leaves/` }),
    create: () => ({ method: "POST", href: `${API_BASE}leaves/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}leaves/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}leaves/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}leaves/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}leaves/${code}/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}leaves/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}leaves/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}leaves/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}leaves/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}leaves/export/` }),
  },
  members: {
    list: () => ({ method: "GET", href: `${API_BASE}members/` }),
    options: () => ({ method: "GET", href: `${API_BASE}members/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}members/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}members/${code}/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}members/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}members/export/` }),
    assignTeam: (code) => ({ method: "POST", href: `${API_BASE}members/${code}/assign-team/` }),
  },
  groups: {
    list: () => ({ method: "GET", href: `${API_BASE}groups/` }),
    create: () => ({ method: "POST", href: `${API_BASE}groups/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}groups/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}groups/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}groups/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}groups/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}groups/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}groups/${code}/deactivate/` }),
    members: (code) => ({ method: "GET", href: `${API_BASE}groups/${code}/members/` }),
    assignMember: (code) => ({ method: "POST", href: `${API_BASE}groups/${code}/members/` }),
    unassignMember: (code, memberCode) => ({
      method: "DELETE",
      href: `${API_BASE}groups/${code}/members/${memberCode}/`,
    }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}groups/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}groups/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}groups/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}groups/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}groups/export/` }),
  },
  permissions: {
    categories: () => ({ method: "GET", href: `${API_BASE}permissions/categories/` }),
    groupList: (groupCode) => ({
      method: "GET",
      href: `${API_BASE}permissions/groups/${groupCode}/`,
    }),
    groupAssign: (groupCode) => ({
      method: "POST",
      href: `${API_BASE}permissions/groups/${groupCode}/`,
    }),
    groupUpdate: (groupCode, code) => ({
      method: "PATCH",
      href: `${API_BASE}permissions/groups/${groupCode}/${code}/`,
    }),
    groupRemove: (groupCode, code) => ({
      method: "DELETE",
      href: `${API_BASE}permissions/groups/${groupCode}/${code}/`,
    }),
    userList: (userCode) => ({
      method: "GET",
      href: `${API_BASE}permissions/users/${userCode}/`,
    }),
    userAssign: (userCode) => ({
      method: "POST",
      href: `${API_BASE}permissions/users/${userCode}/`,
    }),
    userUpdate: (userCode, code) => ({
      method: "PATCH",
      href: `${API_BASE}permissions/users/${userCode}/${code}/`,
    }),
    userRemove: (userCode, code) => ({
      method: "DELETE",
      href: `${API_BASE}permissions/users/${userCode}/${code}/`,
    }),
    userEffective: (userCode) => ({
      method: "GET",
      href: `${API_BASE}permissions/users/${userCode}/effective/`,
    }),
  },
  fy: {
    list: () => ({ method: "GET", href: `${API_BASE}fy/` }),
    create: () => ({ method: "POST", href: `${API_BASE}fy/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}fy/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}fy/options/` }),
    active: () => ({ method: "GET", href: `${API_BASE}fy/active/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}fy/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}fy/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}fy/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}fy/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}fy/${code}/deactivate/` }),
    setActive: (code) => ({ method: "POST", href: `${API_BASE}fy/${code}/set-active/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}fy/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}fy/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}fy/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}fy/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}fy/export/` }),
  },
  sprints: {
    list: () => ({ method: "GET", href: `${API_BASE}sprints/` }),
    create: () => ({ method: "POST", href: `${API_BASE}sprints/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}sprints/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}sprints/options/` }),
    months: () => ({ method: "GET", href: `${API_BASE}sprints/months/` }),
    active: () => ({ method: "GET", href: `${API_BASE}sprints/active/` }),
    generate: () => ({ method: "POST", href: `${API_BASE}sprints/generate/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}sprints/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}sprints/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}sprints/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}sprints/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}sprints/${code}/deactivate/` }),
    setActive: (code) => ({ method: "POST", href: `${API_BASE}sprints/${code}/set-active/` }),
    close: (code) => ({ method: "POST", href: `${API_BASE}sprints/${code}/close/` }),
    capacity: (code) => ({ method: "GET", href: `${API_BASE}sprints/${code}/capacity/` }),
    capacityRebuild: (code) => ({
      method: "POST",
      href: `${API_BASE}sprints/${code}/capacity/rebuild/`,
    }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}sprints/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}sprints/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}sprints/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}sprints/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}sprints/export/` }),
    forecastTemplate: (sprintCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/forecast/template/`,
    }),
    forecastUpload: (sprintCode, teamCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${teamCode}/upload/`,
    }),
    forecastImports: (sprintCode, teamCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${teamCode}/imports/`,
    }),
    forecastImportDetail: (sprintCode, importCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/`,
    }),
    forecastImportRows: (sprintCode, importCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/rows/`,
    }),
    forecastImportRowCreate: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/rows/`,
    }),
    forecastImportRowUpdate: (sprintCode, importCode, rowCode) => ({
      method: "PATCH",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/rows/${rowCode}/`,
    }),
    forecastImportRowDelete: (sprintCode, importCode, rowCode) => ({
      method: "DELETE",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/rows/${rowCode}/`,
    }),
    forecastImportReview: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/review/`,
    }),
    forecastImportConfirm: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/forecast/${importCode}/confirm/`,
    }),
    forecastReviewComplete: (sprintCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/forecast/review-complete/`,
    }),
    actualsTemplate: (sprintCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/actuals/template/`,
    }),
    actualsUpload: (sprintCode, teamCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${teamCode}/upload/`,
    }),
    actualsImports: (sprintCode, teamCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${teamCode}/imports/`,
    }),
    actualsImportDetail: (sprintCode, importCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/`,
    }),
    actualsImportRows: (sprintCode, importCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/rows/`,
    }),
    actualsImportRowCreate: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/rows/`,
    }),
    actualsImportRowUpdate: (sprintCode, importCode, rowCode) => ({
      method: "PATCH",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/rows/${rowCode}/`,
    }),
    actualsImportRowDelete: (sprintCode, importCode, rowCode) => ({
      method: "DELETE",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/rows/${rowCode}/`,
    }),
    actualsImportReview: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/review/`,
    }),
    actualsImportConfirm: (sprintCode, importCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/${importCode}/confirm/`,
    }),
    actualsReviewComplete: (sprintCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/review-complete/`,
    }),
    actualsProjects: (sprintCode) => ({
      method: "GET",
      href: `${API_BASE}sprints/${sprintCode}/actuals/projects/`,
    }),
    actualsSyncProjectActuals: (sprintCode) => ({
      method: "POST",
      href: `${API_BASE}sprints/${sprintCode}/actuals/sync-project-actuals/`,
    }),
  },
  projectSizes: {
    get: () => ({ method: "GET", href: `${API_BASE}projects/sizes/` }),
    update: () => ({ method: "PATCH", href: `${API_BASE}projects/sizes/` }),
  },
  projectActuals: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/actuals/` }),
    summary: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/actuals/summary/` }),
    config: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/actuals/config/` }),
    updateConfig: (code) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/actuals/config/`,
    }),
  },
  burnTracker: {
    list: () => ({ method: "GET", href: `${API_BASE}projects/burn-tracker/` }),
    markDone: (code) => ({
      method: "POST",
      href: `${API_BASE}projects/burn-tracker/${code}/done/`,
    }),
  },
  projectBudgets: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/budgets/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/budgets/` }),
    detail: (code, budgetCode) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/budgets/${budgetCode}/`,
    }),
    update: (code, budgetCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/budgets/${budgetCode}/`,
    }),
    delete: (code, budgetCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/budgets/${budgetCode}/`,
    }),
    history: (code, budgetCode) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/budgets/${budgetCode}/history/`,
    }),
    lifetime: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/budgets/lifetime/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}projects/budgets/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}projects/budgets/export/` }),
  },
  recharges: {
    summary: (sprintCode) => ({
      method: "GET",
      href: `${API_BASE}recharges/summary/?sprint=${encodeURIComponent(sprintCode)}`,
    }),
    list: (sprintCode, type) => ({
      method: "GET",
      href: `${API_BASE}recharges/?sprint=${encodeURIComponent(sprintCode)}&type=${encodeURIComponent(type)}`,
    }),
    details: (code, groupBy) => ({
      method: "GET",
      href: `${API_BASE}recharges/${encodeURIComponent(code)}/details/?group_by=${encodeURIComponent(groupBy)}`,
    }),
    jira: (code) => ({
      method: "GET",
      href: `${API_BASE}recharges/${encodeURIComponent(code)}/jira/`,
    }),
  },
  rechargeEmails: {
    list: (sprintCode, type) => ({
      method: "GET",
      href: `${API_BASE}recharges/email-review/?sprint=${encodeURIComponent(sprintCode)}&type=${encodeURIComponent(type)}`,
    }),
    triggerAll: () => ({ method: "POST", href: `${API_BASE}recharges/email-review/trigger/` }),
    resend: (code) => ({
      method: "POST",
      href: `${API_BASE}recharges/email-review/${encodeURIComponent(code)}/resend/`,
    }),
  },
  rechargeTypes: {
    list: () => ({ method: "GET", href: `${API_BASE}recharges/types/` }),
    create: () => ({ method: "POST", href: `${API_BASE}recharges/types/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}recharges/types/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}recharges/types/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}recharges/types/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}recharges/types/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}recharges/types/${code}/` }),
    activate: (code) => ({
      method: "POST",
      href: `${API_BASE}recharges/types/${code}/activate/`,
    }),
    deactivate: (code) => ({
      method: "POST",
      href: `${API_BASE}recharges/types/${code}/deactivate/`,
    }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}recharges/types/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}recharges/types/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}recharges/types/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}recharges/types/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}recharges/types/export/` }),
  },
  rechargeProjectGroups: {
    list: () => ({ method: "GET", href: `${API_BASE}recharges/project-groups/` }),
    create: () => ({ method: "POST", href: `${API_BASE}recharges/project-groups/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}recharges/project-groups/stats/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}recharges/project-groups/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}recharges/project-groups/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}recharges/project-groups/${code}/` }),
  },
  projectTypeMappings: {
    list: (rc) => ({ method: "GET", href: `${API_BASE}recharges/types/${rc}/mappings/` }),
    create: (rc) => ({ method: "POST", href: `${API_BASE}recharges/types/${rc}/mappings/` }),
    detail: (rc, id) => ({
      method: "GET",
      href: `${API_BASE}recharges/types/${rc}/mappings/${id}/`,
    }),
    update: (rc, id) => ({
      method: "PATCH",
      href: `${API_BASE}recharges/types/${rc}/mappings/${id}/`,
    }),
    delete: (rc, id) => ({
      method: "DELETE",
      href: `${API_BASE}recharges/types/${rc}/mappings/${id}/`,
    }),
    importSpecs: (rc) => ({
      method: "GET",
      href: `${API_BASE}recharges/types/${rc}/mappings/import/specs/`,
    }),
    importSample: (rc) => ({
      method: "GET",
      href: `${API_BASE}recharges/types/${rc}/mappings/import/sample/`,
    }),
    import: (rc) => ({ method: "POST", href: `${API_BASE}recharges/types/${rc}/mappings/import/` }),
    exportSpecs: (rc) => ({
      method: "GET",
      href: `${API_BASE}recharges/types/${rc}/mappings/export/specs/`,
    }),
    export: (rc) => ({ method: "GET", href: `${API_BASE}recharges/types/${rc}/mappings/export/` }),
  },
  projectTypes: {
    list: () => ({ method: "GET", href: `${API_BASE}projects/types/` }),
    create: () => ({ method: "POST", href: `${API_BASE}projects/types/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}projects/types/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}projects/types/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}projects/types/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}projects/types/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}projects/types/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}projects/types/${code}/activate/` }),
    deactivate: (code) => ({
      method: "POST",
      href: `${API_BASE}projects/types/${code}/deactivate/`,
    }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}projects/types/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}projects/types/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}projects/types/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}projects/types/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}projects/types/export/` }),
  },
  projectStatuses: {
    list: () => ({ method: "GET", href: `${API_BASE}projects/statuses/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}projects/statuses/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}projects/statuses/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}projects/statuses/${code}/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}projects/statuses/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}projects/statuses/export/` }),
  },
  projectSubStatuses: {
    list: (sc) => ({ method: "GET", href: `${API_BASE}projects/statuses/${sc}/substatus/` }),
    create: (sc) => ({ method: "POST", href: `${API_BASE}projects/statuses/${sc}/substatus/` }),
    stats: (sc) => ({ method: "GET", href: `${API_BASE}projects/statuses/${sc}/substatus/stats/` }),
    options: (sc) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/options/`,
    }),
    allOptions: () => ({ method: "GET", href: `${API_BASE}projects/sub-statuses/options/` }),
    detail: (sc, code) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/${code}/`,
    }),
    update: (sc, code) => ({
      method: "PATCH",
      href: `${API_BASE}projects/statuses/${sc}/substatus/${code}/`,
    }),
    delete: (sc, code) => ({
      method: "DELETE",
      href: `${API_BASE}projects/statuses/${sc}/substatus/${code}/`,
    }),
    activate: (sc, code) => ({
      method: "POST",
      href: `${API_BASE}projects/statuses/${sc}/substatus/${code}/activate/`,
    }),
    deactivate: (sc, code) => ({
      method: "POST",
      href: `${API_BASE}projects/statuses/${sc}/substatus/${code}/deactivate/`,
    }),
    reorder: (sc) => ({
      method: "POST",
      href: `${API_BASE}projects/statuses/${sc}/substatus/reorder/`,
    }),
    importSpecs: (sc) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/import/specs/`,
    }),
    importSample: (sc) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/import/sample/`,
    }),
    import: (sc) => ({
      method: "POST",
      href: `${API_BASE}projects/statuses/${sc}/substatus/import/`,
    }),
    exportSpecs: (sc) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/export/specs/`,
    }),
    export: (sc) => ({
      method: "GET",
      href: `${API_BASE}projects/statuses/${sc}/substatus/export/`,
    }),
    importAllSpecs: () => ({
      method: "GET",
      href: `${API_BASE}projects/sub-statuses/import/specs/`,
    }),
    importAllSample: () => ({
      method: "GET",
      href: `${API_BASE}projects/sub-statuses/import/sample/`,
    }),
    importAll: () => ({ method: "POST", href: `${API_BASE}projects/sub-statuses/import/` }),
    exportAllSpecs: () => ({
      method: "GET",
      href: `${API_BASE}projects/sub-statuses/export/specs/`,
    }),
    exportAll: () => ({ method: "GET", href: `${API_BASE}projects/sub-statuses/export/` }),
  },
  businessUnits: {
    list: () => ({ method: "GET", href: `${API_BASE}bu/` }),
    create: () => ({ method: "POST", href: `${API_BASE}bu/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}bu/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}bu/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}bu/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}bu/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}bu/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}bu/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}bu/${code}/deactivate/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}bu/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}bu/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}bu/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}bu/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}bu/export/` }),
  },
  onboarding: {
    submit: () => ({ method: "POST", href: `${API_BASE}onboarding/submit/` }),
    options: () => ({ method: "GET", href: `${API_BASE}onboarding/options/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}onboarding/stats/` }),
    uploadAttachment: (code) => ({
      method: "POST",
      href: `${API_BASE}onboarding/${code}/attachments/`,
    }),
  },
  demands: {
    list: () => ({ method: "GET", href: `${API_BASE}demands/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}demands/${code}/` }),
    accept: (code) => ({ method: "POST", href: `${API_BASE}demands/${code}/accept/` }),
    reject: (code) => ({ method: "POST", href: `${API_BASE}demands/${code}/reject/` }),
    attachments: {
      list: (code) => ({ method: "GET", href: `${API_BASE}demands/${code}/attachments/` }),
      download: (code, attCode) => ({
        method: "GET",
        href: `${API_BASE}demands/${code}/attachments/${attCode}/download/`,
      }),
      delete: (code, attCode) => ({
        method: "DELETE",
        href: `${API_BASE}demands/${code}/attachments/${attCode}/`,
      }),
    },
  },
  products: {
    list: () => ({ method: "GET", href: `${API_BASE}products/` }),
    create: () => ({ method: "POST", href: `${API_BASE}products/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}products/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}products/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}products/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}products/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}products/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}products/${code}/activate/` }),
    deactivate: (code) => ({
      method: "POST",
      href: `${API_BASE}products/${code}/deactivate/`,
    }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}products/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}products/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}products/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}products/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}products/export/` }),
  },
  programmes: {
    list: () => ({ method: "GET", href: `${API_BASE}programmes/` }),
    create: () => ({ method: "POST", href: `${API_BASE}programmes/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}programmes/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}programmes/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}programmes/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}programmes/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}programmes/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}programmes/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}programmes/${code}/deactivate/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}programmes/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}programmes/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}programmes/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}programmes/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}programmes/export/` }),
  },
  projects: {
    list: () => ({ method: "GET", href: `${API_BASE}projects/` }),
    create: () => ({ method: "POST", href: `${API_BASE}projects/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}projects/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}projects/options/` }),
    confidenceOptions: () => ({
      method: "GET",
      href: `${API_BASE}projects/options/?fields=confidence`,
    }),
    priorityOptions: () => ({
      method: "GET",
      href: `${API_BASE}projects/options/?fields=priority`,
    }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}projects/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}projects/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/activate/` }),
    deactivate: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/deactivate/` }),
    importSpecs: () => ({ method: "GET", href: `${API_BASE}projects/import/specs/` }),
    importSample: () => ({ method: "GET", href: `${API_BASE}projects/import/sample/` }),
    import: () => ({ method: "POST", href: `${API_BASE}projects/import/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}projects/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}projects/export/` }),
    collaborators: (code) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/collaborators/`,
    }),
    addCollaborator: (code) => ({
      method: "POST",
      href: `${API_BASE}projects/${code}/collaborators/`,
    }),
    removeCollaborator: (code, teamCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/collaborators/${teamCode}/`,
    }),
    labelsOptions: () => ({ method: "GET", href: `${API_BASE}projects/labels/options/` }),
  },
  projectFollowers: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/followers/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/followers/` }),
    delete: (code, followerCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/followers/${followerCode}/`,
    }),
  },
  projectComments: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/comments/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/comments/` }),
    update: (code, commentCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/comments/${commentCode}/`,
    }),
    delete: (code, commentCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/comments/${commentCode}/`,
    }),
    pin: (code, commentCode) => ({
      method: "POST",
      href: `${API_BASE}projects/${code}/comments/${commentCode}/pin/`,
    }),
    unpin: (code, commentCode) => ({
      method: "POST",
      href: `${API_BASE}projects/${code}/comments/${commentCode}/unpin/`,
    }),
  },
  projectContacts: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/contacts/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/contacts/` }),
    update: (code, contactCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/contacts/${contactCode}/`,
    }),
    delete: (code, contactCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/contacts/${contactCode}/`,
    }),
  },
  projectTags: {
    list: (projectCode) => ({ method: "GET", href: `${API_BASE}projects/${projectCode}/tags/` }),
    create: (projectCode) => ({ method: "POST", href: `${API_BASE}projects/${projectCode}/tags/` }),
    delete: (projectCode, tagCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${projectCode}/tags/${tagCode}/`,
    }),
  },
  projectEstimates: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/estimates/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/estimates/` }),
    detail: (code, estCode) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/estimates/${estCode}/`,
    }),
    update: (code, estCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/estimates/${estCode}/`,
    }),
    delete: (code, estCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/estimates/${estCode}/`,
    }),
    history: (code, estCode) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/estimates/${estCode}/history/`,
    }),
  },
  projectLinks: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/links/` }),
    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/links/` }),
    update: (code, linkCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/links/${linkCode}/`,
    }),
    delete: (code, linkCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/links/${linkCode}/`,
    }),
  },
  projectAttachments: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/attachments/` }),
    upload: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/attachments/` }),
    delete: (code, attachmentCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/attachments/${attachmentCode}/`,
    }),
    download: (code, attachmentCode) =>
      `${API_BASE}projects/${code}/attachments/${attachmentCode}/download/`,
  },
  projectLabels: {
    list: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/labels/` }),
    options: () => ({ method: "GET", href: `${API_BASE}projects/labels/options/` }),

    create: (code) => ({ method: "POST", href: `${API_BASE}projects/${code}/labels/` }),
    suggest: (code) => ({ method: "GET", href: `${API_BASE}projects/${code}/labels/suggest/` }),
    detail: (code, labelCode) => ({
      method: "GET",
      href: `${API_BASE}projects/${code}/labels/${labelCode}/`,
    }),
    update: (code, labelCode) => ({
      method: "PATCH",
      href: `${API_BASE}projects/${code}/labels/${labelCode}/`,
    }),
    delete: (code, labelCode) => ({
      method: "DELETE",
      href: `${API_BASE}projects/${code}/labels/${labelCode}/`,
    }),
    setDefault: (code, labelCode) => ({
      method: "POST",
      href: `${API_BASE}projects/${code}/labels/${labelCode}/set-default/`,
    }),
  },
  tags: {
    list: () => ({ method: "GET", href: `${API_BASE}tags/` }),
    create: () => ({ method: "POST", href: `${API_BASE}tags/` }),
    exportSpecs: () => ({ method: "GET", href: `${API_BASE}tags/export/specs/` }),
    export: () => ({ method: "GET", href: `${API_BASE}tags/export/` }),
  },
  setup: {
    defaults: () => ({ method: "GET", href: `${API_BASE}setup/` }),
    setup: () => ({ method: "POST", href: `${API_BASE}setup/` }),
    status: () => ({ method: "GET", href: `${API_BASE}setup/status/` }),
    dbTest: () => ({ method: "POST", href: `${API_BASE}setup/test/db/` }),
    emailTest: () => ({ method: "POST", href: `${API_BASE}setup/test/email/` }),
    samlTest: () => ({ method: "POST", href: `${API_BASE}setup/test/saml/` }),
    oauthTest: () => ({ method: "POST", href: `${API_BASE}setup/test/oauth/` }),
    genKey: () => ({ method: "POST", href: `${API_BASE}setup/gen-key/` }),
  },
  aiConfig: {
    get: () => ({ method: "GET", href: `${API_BASE}ai/config/` }),
    update: () => ({ method: "PATCH", href: `${API_BASE}ai/config/` }),
  },
  securityConfig: {
    get: () => ({ method: "GET", href: `${API_BASE}security/config/` }),
    update: () => ({ method: "PATCH", href: `${API_BASE}security/config/` }),
  },
  wins: {
    list: () => ({ method: "GET", href: `${API_BASE}wins/` }),
    create: () => ({ method: "POST", href: `${API_BASE}wins/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}wins/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}wins/${code}/` }),
    reviewComplete: (code) => ({
      method: "POST",
      href: `${API_BASE}wins/${code}/review-complete/`,
    }),
    reviewPdf: (code) => ({
      method: "GET",
      href: `${API_BASE}wins/${code}/review-pdf/`,
    }),
    sendReview: (code) => ({
      method: "POST",
      href: `${API_BASE}wins/${code}/send-review/`,
    }),
    entries: {
      list: (winCode) => ({
        method: "GET",
        href: `${API_BASE}wins/${winCode}/entries/`,
      }),
      create: (winCode) => ({
        method: "POST",
        href: `${API_BASE}wins/${winCode}/entries/`,
      }),
      update: (winCode, code) => ({
        method: "PATCH",
        href: `${API_BASE}wins/${winCode}/entries/${code}/`,
      }),
      delete: (winCode, code) => ({
        method: "DELETE",
        href: `${API_BASE}wins/${winCode}/entries/${code}/`,
      }),
      suggest: (winCode) => ({
        method: "POST",
        href: `${API_BASE}wins/${winCode}/entries/suggest/`,
      }),
    },
    options: () => ({ method: "GET", href: `${API_BASE}wins/options/` }),
    monthly: {
      list: () => ({ method: "GET", href: `${API_BASE}wins/monthly/` }),
      create: () => ({ method: "POST", href: `${API_BASE}wins/monthly/` }),
      options: () => ({ method: "GET", href: `${API_BASE}wins/monthly/options/` }),
      detail: (code) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/${code}/`,
      }),
      delete: (code) => ({
        method: "DELETE",
        href: `${API_BASE}wins/monthly/${code}/`,
      }),
      previewTeams: (code) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/${code}/preview-teams/`,
      }),
      previewSurvey: (code, phase, teamCode) => {
        const params = new URLSearchParams({ phase });
        if (teamCode) params.set("team", teamCode);
        return {
          method: "GET",
          href: `${API_BASE}wins/monthly/${code}/preview-survey/?${params.toString()}`,
        };
      },
      surveys: (code) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/${code}/surveys/`,
      }),
      results: (code) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/${code}/results/`,
      }),
      launchPhase1: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/launch-phase1/`,
      }),
      completePhase1: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/complete-phase1/`,
      }),
      launchPhase2: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/launch-phase2/`,
      }),
      completePhase2: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/complete-phase2/`,
      }),
      declare: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/declare/`,
      }),
      resultsPdf: (code) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/${code}/results-pdf/`,
      }),
      sendResults: (code) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/${code}/send-results/`,
      }),
      surveyAdminData: (surveyCode) => ({
        method: "GET",
        href: `${API_BASE}wins/monthly/surveys/${surveyCode}/admin-data/`,
      }),
      overrideSurvey: (surveyCode) => ({
        method: "POST",
        href: `${API_BASE}wins/monthly/surveys/${surveyCode}/override/`,
      }),
      recipients: {
        list: () => ({
          method: "GET",
          href: `${API_BASE}wins/monthly/recipients/`,
        }),
        create: () => ({
          method: "POST",
          href: `${API_BASE}wins/monthly/recipients/`,
        }),
        update: (code) => ({
          method: "PATCH",
          href: `${API_BASE}wins/monthly/recipients/${code}/`,
        }),
        delete: (code) => ({
          method: "DELETE",
          href: `${API_BASE}wins/monthly/recipients/${code}/`,
        }),
      },
      survey: {
        get: (token) => ({
          method: "GET",
          href: `${API_BASE}wins/monthly/survey/${token}/`,
        }),
        submit: (token) => ({
          method: "POST",
          href: `${API_BASE}wins/monthly/survey/${token}/submit/`,
        }),
      },
    },
  },
  winsConfig: {
    get: () => ({ method: "GET", href: `${API_BASE}wins/config/` }),
    update: () => ({ method: "PATCH", href: `${API_BASE}wins/config/` }),
  },
  notifications: {
    list: () => ({ method: "GET", href: `${API_BASE}notifications/` }),
    create: () => ({ method: "POST", href: `${API_BASE}notifications/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}notifications/${code}/` }),
    markRead: (code) => ({
      method: "POST",
      href: `${API_BASE}notifications/${code}/read/`,
    }),
    markUnread: (code) => ({
      method: "POST",
      href: `${API_BASE}notifications/${code}/unread/`,
    }),
    dismiss: (code) => ({
      method: "POST",
      href: `${API_BASE}notifications/${code}/dismiss/`,
    }),
    markAllRead: () => ({
      method: "POST",
      href: `${API_BASE}notifications/mark-all-read/`,
    }),
    unreadCount: () => ({ method: "GET", href: `${API_BASE}notifications/unread-count/` }),
    preferences: {
      list: () => ({ method: "GET", href: `${API_BASE}notifications/preferences/` }),
      update: (category) => ({
        method: "PATCH",
        href: `${API_BASE}notifications/preferences/${category}/`,
      }),
    },
  },
  toDo: {
    list: () => ({ method: "GET", href: `${API_BASE}to-do/` }),
    create: () => ({ method: "POST", href: `${API_BASE}to-do/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}to-do/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}to-do/${code}/` }),
    complete: (code) => ({
      method: "POST",
      href: `${API_BASE}to-do/${code}/complete/`,
    }),
    reopen: (code) => ({
      method: "POST",
      href: `${API_BASE}to-do/${code}/reopen/`,
    }),
    openCount: () => ({ method: "GET", href: `${API_BASE}to-do/open-count/` }),
    dueReminders: () => ({
      method: "GET",
      href: `${API_BASE}to-do/due-reminders/`,
    }),
    preferences: {
      list: () => ({ method: "GET", href: `${API_BASE}to-do/preferences/` }),
      update: (category) => ({
        method: "PATCH",
        href: `${API_BASE}to-do/preferences/${category}/`,
      }),
    },
  },
  resourcePlans: {
    list: () => ({ method: "GET", href: `${API_BASE}resource-plans/` }),
    create: () => ({ method: "POST", href: `${API_BASE}resource-plans/` }),
    stats: () => ({ method: "GET", href: `${API_BASE}resource-plans/stats/` }),
    options: () => ({ method: "GET", href: `${API_BASE}resource-plans/options/` }),
    detail: (code) => ({ method: "GET", href: `${API_BASE}resource-plans/${code}/` }),
    update: (code) => ({ method: "PATCH", href: `${API_BASE}resource-plans/${code}/` }),
    delete: (code) => ({ method: "DELETE", href: `${API_BASE}resource-plans/${code}/` }),
    activate: (code) => ({ method: "POST", href: `${API_BASE}resource-plans/${code}/activate/` }),
    deactivate: (code) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/deactivate/`,
    }),
    comments: (code) => ({ method: "GET", href: `${API_BASE}resource-plans/${code}/comments/` }),
    commentCreate: (code) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/comments/`,
    }),
    commentDetail: (code, commentCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/comments/${commentCode}/`,
    }),
    commentUpdate: (code, commentCode) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/comments/${commentCode}/`,
    }),
    commentDelete: (code, commentCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/comments/${commentCode}/`,
    }),
    commentPin: (code, commentCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/comments/${commentCode}/pin/`,
    }),
    commentUnpin: (code, commentCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/comments/${commentCode}/unpin/`,
    }),
    versionCreate: (code) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/`,
    }),
    versionHistory: (code) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/history/`,
    }),
    versionDetail: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/`,
    }),
    versionDelete: (code, version) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/`,
    }),
    versionActivate: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/activate/`,
    }),
    versionRestore: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/restore/`,
    }),
    versionLock: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/lock/`,
    }),
    engineJobsList: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/engine-jobs/`,
    }),
    engineJobsCreate: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/engine-jobs/`,
    }),
    engineJobDetail: (code, version, jobCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/engine-jobs/${jobCode}/`,
    }),
    engineJobDelete: (code, version, jobCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/engine-jobs/${jobCode}/`,
    }),
    versionProjectsUnmapped: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/unmapped/`,
    }),
    versionProjectBudget: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/budget/`,
    }),
    versionProjectCreate: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/`,
    }),
    versionProjectsList: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/`,
    }),
    versionProjectDelete: (code, version, projectVersionCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/`,
    }),
    versionProjectConfigGet: (code, version, projectVersionCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/`,
    }),
    versionProjectConfigUpdate: (code, version, projectVersionCode) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/`,
    }),
    versionProjectResync: (code, version, projectVersionCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/resync/`,
    }),
    versionProjectBudgetReleasesList: (code, version, projectVersionCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/budget-releases/`,
    }),
    versionProjectBudgetReleasesCreate: (code, version, projectVersionCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/budget-releases/`,
    }),
    versionProjectBudgetReleasesUpdate: (
      code,
      version,
      projectVersionCode,
      budgetReleaseVersionCode,
    ) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/budget-releases/${budgetReleaseVersionCode}/`,
    }),
    versionProjectBudgetReleasesDelete: (
      code,
      version,
      projectVersionCode,
      budgetReleaseVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/budget-releases/${budgetReleaseVersionCode}/`,
    }),
    versionProjectTeamsList: (code, version, projectVersionCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/`,
    }),
    versionProjectTeamCreate: (code, version, projectVersionCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/`,
    }),
    versionProjectTeamUpdate: (code, version, projectVersionCode, teamVersionCode) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/`,
    }),
    versionProjectTeamDelete: (code, version, projectVersionCode, teamVersionCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/`,
    }),
    versionProjectTeamPhasesList: (code, version, projectVersionCode, teamVersionCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/`,
    }),
    versionProjectTeamPhaseCreate: (code, version, projectVersionCode, teamVersionCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/`,
    }),
    versionProjectTeamPhaseUpdate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/`,
    }),
    versionProjectTeamPhaseDelete: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/`,
    }),
    versionProjectTeamPhaseSegmentsList: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/segments/`,
    }),
    versionProjectTeamPhaseSegmentCreate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/segments/`,
    }),
    versionProjectTeamPhaseSegmentDelete: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      segmentVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/segments/${segmentVersionCode}/`,
    }),
    versionProjectTeamPhaseDependencyAvailablePredecessors: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/dependencies/available-predecessors/`,
    }),
    versionProjectTeamPhaseDependenciesList: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/dependencies/`,
    }),
    versionProjectTeamPhaseDependencyCreate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/dependencies/`,
    }),
    versionProjectTeamPhaseDependencyUpdate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      dependencyVersionCode,
    ) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/dependencies/${dependencyVersionCode}/`,
    }),
    versionProjectTeamPhaseDependencyDelete: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      dependencyVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/dependencies/${dependencyVersionCode}/`,
    }),
    versionProjectTeamPhasePausesList: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/pauses/`,
    }),
    versionProjectTeamPhasePauseCreate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/pauses/`,
    }),
    versionProjectTeamPhasePauseUpdate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      pauseVersionCode,
    ) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/pauses/${pauseVersionCode}/`,
    }),
    versionProjectTeamPhasePauseDelete: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      pauseVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/pauses/${pauseVersionCode}/`,
    }),
    versionProjectTeamPhaseAssignmentsList: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/assignments/`,
    }),
    versionProjectTeamPhaseAssignmentCreate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
    ) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/assignments/`,
    }),
    versionProjectTeamPhaseAssignmentUpdate: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      assignmentVersionCode,
    ) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/assignments/${assignmentVersionCode}/`,
    }),
    versionProjectTeamPhaseAssignmentDelete: (
      code,
      version,
      projectVersionCode,
      teamVersionCode,
      phaseVersionCode,
      assignmentVersionCode,
    ) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/projects/${projectVersionCode}/teams/${teamVersionCode}/phases/${phaseVersionCode}/assignments/${assignmentVersionCode}/`,
    }),
    allocationSetsList: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/`,
    }),
    allocationSetDetail: (code, version, allocationSetCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/`,
    }),
    allocationSetActivate: (code, version, allocationSetCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/activate/`,
    }),
    allocationOverride: (code, version, allocationSetCode, allocationCode) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/allocations/${allocationCode}/override/`,
    }),
    gridCapacity: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/grid/capacity/`,
    }),
    gridAbsences: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/grid/absences/`,
    }),
    gridAllocatedCapacity: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/grid/allocated-capacity/`,
    }),
    gridAllocations: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/grid/allocations/`,
    }),
    conflictsList: (code, version, allocationSetCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/conflicts/`,
    }),
    conflictDetail: (code, version, allocationSetCode, conflictCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/conflicts/${conflictCode}/`,
    }),
    conflictResolve: (code, version, allocationSetCode, conflictCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/conflicts/${conflictCode}/resolve/`,
    }),
    manpowerRequestsList: (code, version, allocationSetCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/manpower-requests/`,
    }),
    manpowerRequestDetail: (code, version, allocationSetCode, requestCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/manpower-requests/${requestCode}/`,
    }),
    manpowerRequestHire: (code, version, allocationSetCode, requestCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/manpower-requests/${requestCode}/hire/`,
    }),
    manpowerRequestRebalance: (code, version, allocationSetCode, requestCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/manpower-requests/${requestCode}/rebalance/`,
    }),
    manpowerRequestDismiss: (code, version, allocationSetCode, requestCode) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/allocation-sets/${allocationSetCode}/manpower-requests/${requestCode}/dismiss/`,
    }),
    placeholderLeavesList: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/placeholder-leaves/`,
    }),
    placeholderLeaveUpdate: (code, version, leaveCode) => ({
      method: "PATCH",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/placeholder-leaves/${leaveCode}/`,
    }),
    placeholderLeaveDelete: (code, version, leaveCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/placeholder-leaves/${leaveCode}/`,
    }),
    placeholderLeavesRegenerate: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/placeholder-leaves/regenerate/`,
    }),
    utilisationTeams: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/utilisation/teams/`,
    }),
    utilisationMembers: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/utilisation/members/`,
    }),
    utilisationProgrammes: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/utilisation/programmes/`,
    }),
    snapshotsList: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/`,
    }),
    snapshotsCreate: (code, version) => ({
      method: "POST",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/`,
    }),
    snapshotsCompare: (code, version) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/compare/`,
    }),
    snapshotDetail: (code, version, snapshotCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/${snapshotCode}/`,
    }),
    snapshotDelete: (code, version, snapshotCode) => ({
      method: "DELETE",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/${snapshotCode}/`,
    }),
    snapshotAllocations: (code, version, snapshotCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/${snapshotCode}/allocations/`,
    }),
    snapshotAllocationFilterOptions: (code, version, snapshotCode) => ({
      method: "GET",
      href: `${API_BASE}resource-plans/${code}/versions/v${version}/snapshots/${snapshotCode}/allocations/filter-options/`,
    }),
  },
  reports: {
    standardList: () => ({ method: "GET", href: `${API_BASE}reports/standard/` }),
    standardDetail: (slug) => ({
      method: "GET",
      href: `${API_BASE}reports/standard/${slug}/`,
    }),
    weeklyWinsData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/weekly-wins/data/`,
    }),
    weeklyWinsExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/weekly-wins/export/specs/`,
    }),
    weeklyWinsExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/weekly-wins/export/`,
    }),
    monthlyWinsData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-wins/data/`,
    }),
    monthlyWinsExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-wins/export/specs/`,
    }),
    monthlyWinsExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-wins/export/`,
    }),
    sprintForecastVsActualsData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/sprint-forecast-vs-actuals/data/`,
    }),
    sprintForecastVsActualsExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/sprint-forecast-vs-actuals/export/specs/`,
    }),
    sprintForecastVsActualsExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/sprint-forecast-vs-actuals/export/`,
    }),
    demandVsCapacityData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/demand-vs-capacity/data/`,
    }),
    demandVsCapacityExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/demand-vs-capacity/export/specs/`,
    }),
    demandVsCapacityExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/demand-vs-capacity/export/`,
    }),
    demandVsCapacityConfigList: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/demand-vs-capacity/configs/`,
    }),
    demandVsCapacityConfigCreate: () => ({
      method: "POST",
      href: `${API_BASE}reports/standard/demand-vs-capacity/configs/`,
    }),
    demandVsCapacityConfigDetail: (code) => ({
      method: "GET",
      href: `${API_BASE}reports/standard/demand-vs-capacity/configs/${code}/`,
    }),
    demandVsCapacityConfigUpdate: (code) => ({
      method: "PATCH",
      href: `${API_BASE}reports/standard/demand-vs-capacity/configs/${code}/`,
    }),
    demandVsCapacityConfigDelete: (code) => ({
      method: "DELETE",
      href: `${API_BASE}reports/standard/demand-vs-capacity/configs/${code}/`,
    }),
    kpiEstimateAccuracyData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/data/`,
    }),
    kpiEstimateAccuracyExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/export/specs/`,
    }),
    kpiEstimateAccuracyExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/export/`,
    }),
    kpiEstimateAccuracyConfigList: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/configs/`,
    }),
    kpiEstimateAccuracyConfigCreate: () => ({
      method: "POST",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/configs/`,
    }),
    kpiEstimateAccuracyConfigDetail: (code) => ({
      method: "GET",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/configs/${code}/`,
    }),
    kpiEstimateAccuracyConfigUpdate: (code) => ({
      method: "PATCH",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/configs/${code}/`,
    }),
    kpiEstimateAccuracyConfigDelete: (code) => ({
      method: "DELETE",
      href: `${API_BASE}reports/standard/kpi-estimate-accuracy/configs/${code}/`,
    }),
    monthlyFinanceReportData: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-finance-report/data/`,
    }),
    monthlyFinanceReportExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-finance-report/export/specs/`,
    }),
    monthlyFinanceReportExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/standard/monthly-finance-report/export/`,
    }),
    customList: () => ({ method: "GET", href: `${API_BASE}reports/custom/` }),
    customCreate: () => ({ method: "POST", href: `${API_BASE}reports/custom/` }),
    customDetail: (code) => ({
      method: "GET",
      href: `${API_BASE}reports/custom/${code}/`,
    }),
    customUpdate: (code) => ({
      method: "PATCH",
      href: `${API_BASE}reports/custom/${code}/`,
    }),
    customDelete: (code) => ({
      method: "DELETE",
      href: `${API_BASE}reports/custom/${code}/`,
    }),
    customDataSources: () => ({
      method: "GET",
      href: `${API_BASE}reports/custom/data-sources/`,
    }),
    customPreview: () => ({
      method: "POST",
      href: `${API_BASE}reports/custom/preview/`,
    }),
    customExecute: (code) => ({
      method: "POST",
      href: `${API_BASE}reports/custom/${code}/execute/`,
    }),
    customExportSpecs: () => ({
      method: "GET",
      href: `${API_BASE}reports/custom/export/specs/`,
    }),
    customExport: () => ({
      method: "GET",
      href: `${API_BASE}reports/custom/export/`,
    }),
    customShareList: (code) => ({
      method: "GET",
      href: `${API_BASE}reports/custom/${code}/share/`,
    }),
    customShareCreate: (code) => ({
      method: "POST",
      href: `${API_BASE}reports/custom/${code}/share/`,
    }),
    customShareDelete: (code, memberCode) => ({
      method: "DELETE",
      href: `${API_BASE}reports/custom/${code}/share/${memberCode}/`,
    }),
  },
};
