<template>
  <div class="settings-page">
    <!-- 左侧导航 -->
    <aside class="sidenav">
      <nav class="sidenav-list">
        <button v-for="item in navItems" :key="item.key"
          :class="['sidenav-item', { active: activeTab === item.key }]"
          @click="activeTab = item.key">
          <component :is="item.icon" :size="18" />
          <div class="sidenav-text">
            <span class="sidenav-label">{{ item.label }}</span>
            <span class="sidenav-desc">{{ item.desc }}</span>
          </div>
          <ChevronRight :size="14" class="sidenav-arrow" />
        </button>
      </nav>
      <div class="sidenav-footer">
        <div class="sync-banner">
          <img src="/field-bg.jpg" alt="" class="sync-bg" />
          <div class="sync-overlay">
            <div class="sync-row">
              <span class="sync-dot"></span>
              <span class="sync-text">数据同步正常</span>
              <ChevronRight :size="12" />
            </div>
            <span class="sync-sub">最后同步：{{ userStats.last_sync ? '刚刚' : '2 分钟前' }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 中间：用户信息 -->
    <div class="mid-col">
      <div class="profile-card">
        <div class="avatar-ring">
          <img src="/logo.jpg" alt="avatar" class="avatar-img" />
        </div>
        <div class="profile-name">{{ userProfile.username || userInfo.id || '农户用户' }}</div>
        <span class="role-badge">{{ userProfile.role === 'admin' ? '管理员' : '合作社成员' }}</span>
        <div class="profile-stats">
          <div class="pstat">
            <span class="pstat-num">{{ userStats.service_days ?? '--' }}</span>
            <span class="pstat-label">已服务天数</span>
          </div>
          <div class="pstat-divider"></div>
          <div class="pstat">
            <span class="pstat-num">{{ userStats.field_count ?? '--' }}</span>
            <span class="pstat-label">管理田块</span>
          </div>
        </div>
      </div>

      <div class="security-card">
        <div class="sec-header">
          <div class="sec-icon"><ShieldCheck :size="20" /></div>
          <div>
            <div class="sec-title">账户安全等级</div>
            <div :class="['sec-level', securityLevel.class]">{{ securityLevel.text }}</div>
          </div>
        </div>
        <div class="sec-bar">
          <div class="sec-bar-fill" :style="{ width: securityLevel.percent + '%' }"></div>
        </div>
        <p class="sec-tip">{{ securityLevel.tip }}</p>
        <a class="sec-link" v-if="securityLevel.percent < 80" @click="activeTab = 'account'">去开启</a>
      </div>
    </div>

    <!-- 右侧：主内容 -->
    <div class="main-col">
      <!-- ===== 账户与安全 ===== -->
      <template v-if="activeTab === 'account'">
        <div class="main-head">
          <h1>账户与安全</h1>
          <p>管理您的账户信息和安全设置，保障账户安全</p>
        </div>
        <div class="content-grid">
          <div class="content-left">
            <div class="card">
              <div class="card-head"><User :size="16" /> 账户信息</div>
              <div class="info-rows">
                <div class="info-row">
                  <span class="info-label">用户ID</span>
                  <span class="info-val mono">{{ userInfo.id || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">角色</span>
                  <span class="info-val">{{ userProfile.role === 'admin' ? '管理员' : '农户' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">手机号</span>
                  <span class="info-val">{{ userProfile.phone || '未设置' }}
                    <button class="btn-inline" @click="openPhoneModal">修改</button>
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">实名认证</span>
                  <span class="info-val">
                    <span v-if="userProfile.verified" class="verified"><CheckCircle :size="14" /> 已认证</span>
                    <span v-else class="unverified">未认证 <button class="btn-inline" @click="openVerifyModal">去认证</button></span>
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">注册时间</span>
                  <span class="info-val mono">{{ userInfo.created || '—' }}</span>
                </div>
              </div>
            </div>
            <div class="card">
              <div class="card-head"><Lock :size="16" /> 修改密码</div>
              <p class="card-desc">定期修改密码，保障账户安全</p>
              <div class="form-group">
                <label>当前密码</label>
                <div class="input-wrap">
                  <input v-model="pwd.old" :type="showPwd ? 'text' : 'password'" placeholder="请输入当前密码" />
                  <button class="eye-btn" @click="showPwd = !showPwd"><Eye v-if="!showPwd" :size="16" /><EyeOff v-else :size="16" /></button>
                </div>
              </div>
              <div class="form-group">
                <label>新密码</label>
                <div class="input-wrap">
                  <input v-model="pwd.new1" :type="showPwd ? 'text' : 'password'" placeholder="请输入新密码（6-20位）" />
                  <button class="eye-btn" @click="showPwd = !showPwd"><Eye v-if="!showPwd" :size="16" /><EyeOff v-else :size="16" /></button>
                </div>
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <div class="input-wrap">
                  <input v-model="pwd.new2" :type="showPwd ? 'text' : 'password'" placeholder="请再次输入新密码" />
                  <button class="eye-btn" @click="showPwd = !showPwd"><Eye v-if="!showPwd" :size="16" /><EyeOff v-else :size="16" /></button>
                </div>
              </div>
              <button class="btn-green" @click="changePassword" :disabled="!pwd.old || !pwd.new1 || pwd.new1 !== pwd.new2">保存修改</button>
              <span class="action-msg" :class="{ error: pwdMsg.includes('失败') || pwdMsg.includes('不一致') }" v-if="pwdMsg">{{ pwdMsg }}</span>
            </div>
            <div class="security-banner">
              <div class="sb-icon"><Shield :size="28" /></div>
              <div class="sb-body">
                <h3>保护账户安全，从现在开始</h3>
                <p>定期更新密码，开启双重验证，确保您的农业数据安全无忧</p>
                <a class="sb-link" @click="$router.push('/map/help')">了解更多安全建议</a>
              </div>
            </div>
          </div>
          <div class="content-right">
            <div class="card">
              <div class="card-head"><Shield :size="16" /> 安全设置</div>
              <div class="action-list">
                <div class="action-item" @click="showDeviceModal = true">
                  <div class="action-icon"><Monitor :size="18" /></div>
                  <div class="action-info">
                    <span class="action-title">登录设备管理</span>
                    <span class="action-sub">查看和管理您的登录设备</span>
                  </div>
                  <ChevronRight :size="16" class="action-arrow" />
                </div>
                <div class="action-item" @click="toggle2FA">
                  <div class="action-icon"><ShieldCheck :size="18" /></div>
                  <div class="action-info">
                    <span class="action-title">双重验证</span>
                    <span class="action-sub">增加账户安全保护</span>
                  </div>
                  <span :class="['status-tag', userProfile.twoFactor ? 'on' : 'off']">{{ userProfile.twoFactor ? '已开启' : '未开启' }}</span>
                  <ChevronRight :size="16" class="action-arrow" />
                </div>
              </div>
            </div>
            <div class="card">
              <div class="card-head"><Zap :size="16" /> 快速操作</div>
              <div class="action-list">
                <div class="action-item" @click="openPhoneModal">
                  <div class="action-icon"><Smartphone :size="18" /></div>
                  <div class="action-info">
                    <span class="action-title">修改手机号</span>
                    <span class="action-sub">更换绑定的手机号码</span>
                  </div>
                  <ChevronRight :size="16" class="action-arrow" />
                </div>
                <div class="action-item" @click="openVerifyModal">
                  <div class="action-icon"><BadgeCheck :size="18" /></div>
                  <div class="action-info">
                    <span class="action-title">实名认证</span>
                    <span class="action-sub">完成实名认证，提升账户安全</span>
                  </div>
                  <span :class="['status-tag', userProfile.verified ? 'on' : 'off']">{{ userProfile.verified ? '已认证' : '未认证' }}</span>
                  <ChevronRight :size="16" class="action-arrow" />
                </div>
                <div class="action-item" @click="showDeleteModal = true">
                  <div class="action-icon" style="background:#fef2f2;color:#ef4444"><UserX :size="18" /></div>
                  <div class="action-info">
                    <span class="action-title">账号注销</span>
                    <span class="action-sub">永久注销账户，删除所有数据</span>
                  </div>
                  <ChevronRight :size="16" class="action-arrow" />
                </div>
              </div>
            </div>
            <div class="card">
              <div class="card-head"><Headphones :size="16" /> 需要帮助？</div>
              <p class="card-desc">如果您在使用过程中遇到问题</p>
              <button class="btn-outline" @click="$router.push('/map/help')"><PhoneCall :size="14" /> 联系客服</button>
              <div class="help-link" @click="$router.push('/map/help')">
                <HelpCircle :size="14" /> 常见问题 <ChevronRight :size="14" />
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ===== 平台设置 ===== -->
      <template v-if="activeTab === 'platform'">
        <div class="main-head"><h1>平台设置</h1><p>自定义地图、数据源和显示偏好</p></div>
        <div class="card">
          <div class="card-head"><Map :size="16" /> 地图默认设置</div>
          <p class="card-desc">修改后下次进入地图时生效</p>
          <div class="form-grid-3">
            <div class="form-group"><label>默认经度</label><input class="form-input" v-model.number="platformSettings.centerLon" type="number" step="0.01" /></div>
            <div class="form-group"><label>默认纬度</label><input class="form-input" v-model.number="platformSettings.centerLat" type="number" step="0.01" /></div>
            <div class="form-group"><label>默认缩放 (1-18)</label><input class="form-input" v-model.number="platformSettings.zoom" type="number" min="1" max="18" /></div>
          </div>
          <button class="btn-green" @click="savePlatformSettings">保存设置</button>
          <span class="action-msg success" v-if="platformMsg">{{ platformMsg }}</span>
        </div>
        <div class="card">
          <div class="card-head"><Satellite :size="16" /> Google Earth Engine <span :class="['badge', geeStatus === '已连接' ? 'badge-success' : 'badge-warning']">{{ geeStatus }}</span></div>
          <p class="card-desc">GEE 用于获取 Sentinel-2 实时 NDVI 数据。国内需要配置 SOCKS5 代理。</p>
          <div class="form-group"><label>代理地址</label><input class="form-input" v-model="platformSettings.geeProxy" placeholder="socks5://127.0.0.1:10808" /></div>
          <div class="form-actions">
            <button class="btn-green" @click="testGEE" :disabled="testingGEE">{{ testingGEE ? '检测中...' : '检测连接' }}</button>
            <span class="action-msg" :style="{ color: geeTestResult?.startsWith('✓') ? '#16a34a' : '#ef4444' }">{{ geeTestResult }}</span>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><HardDrive :size="16" /> 缓存管理</div>
          <p class="card-desc">清除本地缓存可解决数据显示异常，不影响田块数据</p>
          <button class="btn-outline" @click="clearCache">清除本地缓存</button>
          <span class="action-msg success" v-if="cacheMsg">{{ cacheMsg }}</span>
        </div>
      </template>

      <!-- ===== 农机与设备 ===== -->
      <template v-if="activeTab === 'machinery'">
        <div class="main-head"><h1>农机与设备</h1><p>管理已绑定的农机、北斗设备和无人机</p></div>
        <div class="card">
          <div class="card-head"><Truck :size="16" /> 已绑定设备</div>
          <div class="device-list">
            <div class="device-item" v-for="d in apiDevices" :key="d.id">
              <div class="device-icon" :style="{ background: deviceColor(d.device_type).bg }">
                <component :is="deviceIcon(d.device_type)" :size="20" :style="{ color: deviceColor(d.device_type).color }" />
              </div>
              <div class="device-info">
                <div class="device-name">{{ d.name }}</div>
                <div class="device-meta">{{ d.model || d.device_type }} {{ d.serial_number ? '· ' + d.serial_number : '' }}</div>
              </div>
              <span :class="['badge', d.status === 'online' ? 'badge-success' : 'badge-warning']">{{ d.status === 'online' ? '在线' : '离线' }}</span>
            </div>
            <p v-if="!apiDevices.length" class="empty-text">暂无绑定设备</p>
          </div>
          <button class="btn-outline" style="margin-top:12px" @click="showAddDeviceModal = true">+ 绑定新设备</button>
        </div>
      </template>

      <!-- ===== 通知与消息 ===== -->
      <template v-if="activeTab === 'notify'">
        <div class="main-head"><h1>通知与消息</h1><p>消息管理和通知设置</p></div>
        <div class="card">
          <div class="card-head"><Bell :size="16" /> 通知设置</div>
          <div class="toggle-list">
            <div class="toggle-item" v-for="n in notifySettings" :key="n.type">
              <div><span class="toggle-label">{{ n.label }}</span><span class="toggle-desc">启停该类通知推送</span></div>
              <label class="switch"><input type="checkbox" v-model="n.enabled" @change="saveNotifySetting(n)" /><span class="slider"></span></label>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><Inbox :size="16" /> 最近消息</div>
          <div v-if="notifications.length" class="msg-list">
            <div v-for="n in notifications" :key="n.id" class="msg-item" :class="{ unread: !n.read }" @click="markRead(n.id)">
              <div class="msg-dot" :style="{ background: n.type === 'alert' ? '#ef4444' : n.type === 'info' ? '#3b82f6' : '#16a34a' }"></div>
              <div class="msg-body"><span class="msg-text">{{ n.text }}</span><span class="msg-time">{{ n.time }}</span></div>
            </div>
          </div>
          <p v-else class="empty-text">暂无新消息</p>
        </div>
      </template>

      <!-- ===== 成员与团队 ===== -->
      <template v-if="activeTab === 'team'">
        <div class="main-head"><h1>成员与团队</h1><p>团队成员管理和角色权限</p></div>
        <div class="card">
          <div class="card-head"><Users :size="16" /> 团队成员</div>
          <div class="team-list">
            <div class="team-item" v-for="m in teamMembers" :key="m.id">
              <div class="team-avatar" :style="{ background: stringToColor(m.username) }">{{ m.display_name?.[0] || m.username[0] }}</div>
              <div class="team-info"><span class="team-name">{{ m.display_name || m.username }}</span><span class="team-role">{{ roleLabel(m.role) }}</span></div>
              <span class="team-status" :class="m.status === 'active' ? 'online' : ''">{{ m.status === 'active' ? '在线' : '待激活' }}</span>
              <button class="btn-inline" style="color:#ef4444;border-color:#fecaca;margin-left:8px" @click="removeMember(m.id)">移除</button>
            </div>
            <p v-if="!teamMembers.length" class="empty-text">暂无团队成员</p>
          </div>
          <button class="btn-outline" style="margin-top:12px" @click="showInviteModal = true">+ 邀请成员</button>
        </div>
      </template>

      <!-- ===== 使用与数据 ===== -->
      <template v-if="activeTab === 'usage'">
        <div class="main-head"><h1>使用与数据</h1><p>用量统计和数据导出</p></div>
        <div class="card">
          <div class="card-head"><BarChart3 :size="16" /> 用量统计</div>
          <div class="usage-grid">
            <div class="usage-item"><span class="usage-num">{{ userStats.field_count || 0 }}</span><span class="usage-label">田块数</span></div>
            <div class="usage-item"><span class="usage-num">{{ userStats.total_carbon_tco2e || '0' }} t</span><span class="usage-label">碳汇总量</span></div>
            <div class="usage-item"><span class="usage-num">∞</span><span class="usage-label">API 调用</span></div>
            <div class="usage-item"><span class="usage-num">{{ userStats.service_days || 0 }}</span><span class="usage-label">使用天数</span></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><Download :size="16" /> 数据导出</div>
          <p class="card-desc">导出您的田块数据和分析报告</p>
          <div class="export-list">
            <button class="btn-outline" @click="exportData('fields')">导出田块数据 (JSON)</button>
            <button class="btn-outline" @click="exportData('carbon')">导出碳汇报告 (PDF)</button>
            <button class="btn-outline" @click="exportData('ndvi')">导出 NDVI 时序 (CSV)</button>
          </div>
        </div>
      </template>

      <!-- ===== 关于平台 ===== -->
      <template v-if="activeTab === 'about'">
        <div class="main-head"><h1>关于平台</h1><p>版本信息、数据来源和技术支持</p></div>
        <div class="card">
          <div class="card-head"><Info :size="16" /> 平台信息</div>
          <div class="info-rows">
            <div class="info-row"><span class="info-label">当前版本</span><span class="info-val mono">v0.2.0</span></div>
            <div class="info-row"><span class="info-label">数据源</span><span class="info-val">NASA DEM · 武大CLCD · SoilGrids · OpenWeather · ESA Sentinel-2</span></div>
            <div class="info-row"><span class="info-label">核心算法</span><span class="info-val">AHP+熵权+TOPSIS · RothC碳汇 · CUSUM物候 · A*路径</span></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><Phone :size="16" /> 技术支持</div>
          <div class="info-rows">
            <div class="info-row"><span class="info-label">实验室</span><span class="info-val">东北农业遥感实验室</span></div>
            <div class="info-row"><span class="info-label">邮箱</span><span class="info-val mono">support@agrispatial.cn</span></div>
          </div>
        </div>
        <div class="card" style="border-color:rgba(239,68,68,0.15)">
          <div class="card-head" style="color:#ef4444"><AlertTriangle :size="16" /> 账号操作</div>
          <p class="card-desc">退出后需要重新登录</p>
          <button class="btn-outline" style="color:#ef4444;border-color:#fecaca" @click="logout"><LogOut :size="14" /> 退出登录</button>
        </div>
      </template>
    </div>

    <!-- ========== 弹窗：修改手机号 ========== -->
    <div v-if="showPhoneModal" class="modal-overlay" @click.self="showPhoneModal = false">
      <div class="modal-box">
        <div class="modal-head"><h3>修改手机号</h3><button class="modal-close" @click="showPhoneModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="form-group">
            <label>当前手机号</label>
            <input class="form-input" :value="userProfile.phone || '未设置'" disabled />
          </div>
          <div class="form-group">
            <label>新手机号</label>
            <input class="form-input" v-model="phoneForm.newPhone" placeholder="请输入新手机号" />
          </div>
          <div class="form-group">
            <label>验证码</label>
            <div class="input-with-btn">
              <input class="form-input" v-model="phoneForm.code" placeholder="请输入验证码" />
              <button class="btn-outline" @click="sendCode" :disabled="codeCooldown > 0" style="white-space:nowrap">
                {{ codeCooldown > 0 ? codeCooldown + 's' : '发送验证码' }}
              </button>
            </div>
          </div>
          <p class="form-tip">测试环境验证码固定为 123456</p>
          <p class="form-error" v-if="phoneForm.error">{{ phoneForm.error }}</p>
          <p class="form-success" v-if="phoneForm.success">{{ phoneForm.success }}</p>
          <button class="btn-green btn-block" @click="submitPhone" :disabled="!phoneForm.newPhone || !phoneForm.code || phoneForm.loading">
            {{ phoneForm.loading ? '提交中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ========== 弹窗：实名认证 ========== -->
    <div v-if="showVerifyModal" class="modal-overlay" @click.self="showVerifyModal = false">
      <div class="modal-box">
        <div class="modal-head"><h3>实名认证</h3><button class="modal-close" @click="showVerifyModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="verify-notice">
            <ShieldCheck :size="18" />
            <span>实名认证后可解锁更多平台功能，您的信息将被严格保密。</span>
          </div>
          <div class="form-group">
            <label>真实姓名</label>
            <input class="form-input" v-model="verifyForm.realName" placeholder="请输入身份证上的姓名" />
          </div>
          <div class="form-group">
            <label>身份证号</label>
            <input class="form-input" v-model="verifyForm.idCard" placeholder="请输入18位身份证号" maxlength="18" />
          </div>
          <p class="form-error" v-if="verifyForm.error">{{ verifyForm.error }}</p>
          <p class="form-success" v-if="verifyForm.success">{{ verifyForm.success }}</p>
          <button class="btn-green btn-block" @click="submitVerify" :disabled="!verifyForm.realName || !verifyForm.idCard || verifyForm.loading">
            {{ verifyForm.loading ? '提交中...' : '提交认证' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ========== 弹窗：注销账号 ========== -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-box modal-danger">
        <div class="modal-head"><h3 style="color:#ef4444">账号注销</h3><button class="modal-close" @click="showDeleteModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="delete-warn">
            <AlertTriangle :size="20" />
            <div>
              <strong>此操作不可恢复</strong>
              <p>注销后以下数据将被永久删除：</p>
              <ul>
                <li>所有田块和土壤数据</li>
                <li>碳汇报告和分析记录</li>
                <li>AI 对话历史</li>
                <li>团队和设备绑定信息</li>
              </ul>
            </div>
          </div>
          <div class="form-group">
            <label>登录密码</label>
            <input class="form-input" v-model="deleteForm.password" type="password" placeholder="请输入当前密码" />
          </div>
          <div class="form-group">
            <label>请输入 <strong>确认删除</strong> 以继续</label>
            <input class="form-input" v-model="deleteForm.confirm" placeholder="确认删除" />
          </div>
          <p class="form-error" v-if="deleteForm.error">{{ deleteForm.error }}</p>
          <button class="btn-danger btn-block" @click="submitDelete" :disabled="deleteForm.confirm !== '确认删除' || !deleteForm.password || deleteForm.loading">
            {{ deleteForm.loading ? '处理中...' : '确认注销' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ========== 弹窗：邀请成员 ========== -->
    <div v-if="showInviteModal" class="modal-overlay" @click.self="showInviteModal = false">
      <div class="modal-box">
        <div class="modal-head"><h3>邀请成员</h3><button class="modal-close" @click="showInviteModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input class="form-input" v-model="inviteForm.username" placeholder="输入成员的平台用户名" />
          </div>
          <div class="form-group">
            <label>显示名称（选填）</label>
            <input class="form-input" v-model="inviteForm.displayName" placeholder="如：张技术员" />
          </div>
          <div class="form-group">
            <label>角色</label>
            <select class="form-input" v-model="inviteForm.role">
              <option value="viewer">观察者 — 仅查看</option>
              <option value="editor">编辑者 — 可编辑数据</option>
              <option value="admin">管理员 — 完全权限</option>
            </select>
          </div>
          <p class="form-error" v-if="inviteForm.error">{{ inviteForm.error }}</p>
          <p class="form-success" v-if="inviteForm.success">{{ inviteForm.success }}</p>
          <button class="btn-green btn-block" @click="submitInvite" :disabled="!inviteForm.username || inviteForm.loading">
            {{ inviteForm.loading ? '发送中...' : '发送邀请' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ========== 弹窗：绑定设备 ========== -->
    <div v-if="showAddDeviceModal" class="modal-overlay" @click.self="showAddDeviceModal = false">
      <div class="modal-box">
        <div class="modal-head"><h3>绑定新设备</h3><button class="modal-close" @click="showAddDeviceModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="form-group">
            <label>设备名称</label>
            <input class="form-input" v-model="deviceForm.name" placeholder="如：大疆 T60 植保无人机" />
          </div>
          <div class="form-group">
            <label>设备类型</label>
            <select class="form-input" v-model="deviceForm.deviceType">
              <option value="drone">无人机</option>
              <option value="sensor">传感器</option>
              <option value="gateway">网关</option>
              <option value="tractor">农机</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>型号（选填）</label>
            <input class="form-input" v-model="deviceForm.model" placeholder="设备型号" />
          </div>
          <div class="form-group">
            <label>序列号（选填）</label>
            <input class="form-input" v-model="deviceForm.serialNumber" placeholder="设备序列号" />
          </div>
          <p class="form-error" v-if="deviceForm.error">{{ deviceForm.error }}</p>
          <p class="form-success" v-if="deviceForm.success">{{ deviceForm.success }}</p>
          <button class="btn-green btn-block" @click="submitDevice" :disabled="!deviceForm.name || deviceForm.loading">
            {{ deviceForm.loading ? '绑定中...' : '确认绑定' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ========== 弹窗：登录设备管理 ========== -->
    <div v-if="showDeviceModal" class="modal-overlay" @click.self="showDeviceModal = false">
      <div class="modal-box">
        <div class="modal-head"><h3>登录设备管理</h3><button class="modal-close" @click="showDeviceModal = false"><X :size="18" /></button></div>
        <div class="modal-body">
          <div class="device-list">
            <div class="device-item" v-for="d in loginDevices" :key="d.id">
              <div class="device-icon" :style="{ background: d.is_current ? '#e8f5e9' : '#f5f5f5', color: d.is_current ? '#16a34a' : '#888' }"><Monitor :size="18" /></div>
              <div class="device-info">
                <div class="device-name">{{ d.device_name }} <span v-if="d.is_current" class="badge badge-success" style="margin-left:6px">当前设备</span></div>
                <div class="device-meta">{{ d.ip_address || '未知IP' }} · {{ formatDeviceTime(d.last_seen) }}</div>
              </div>
              <button v-if="!d.is_current" class="btn-inline" style="color:#ef4444;border-color:#fecaca" @click="revokeDevice(d.id)">移除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import {
  Shield, ShieldCheck, Map, Satellite, HardDrive, Truck, Info, Phone,
  LogOut, ChevronRight, AlertTriangle, Tractor, Plane, Radio,
  User, Lock, Eye, EyeOff, CheckCircle, Zap, Monitor, Smartphone,
  BadgeCheck, UserX, Headphones, PhoneCall, HelpCircle,
  Bell, Inbox, Users, BarChart3, Download, X
} from 'lucide-vue-next'

const router = useRouter()
const activeTab = ref('account')
const showPwd = ref(false)
const showDeviceModal = ref(false)
const platformMsg = ref('')
const cacheMsg = ref('')
const geeStatus = ref('未知')
const testingGEE = ref(false)
const geeTestResult = ref('')

// 弹窗控制
const showPhoneModal = ref(false)
const showVerifyModal = ref(false)
const showDeleteModal = ref(false)
const showInviteModal = ref(false)
const showAddDeviceModal = ref(false)

const codeCooldown = ref(0)

const navItems = [
  { key: 'account', icon: Shield, label: '账户与安全', desc: '密码、手机、实名认证' },
  { key: 'platform', icon: Map, label: '平台设置', desc: '地图、数据源、缓存' },
  { key: 'machinery', icon: Truck, label: '农机与设备', desc: '已绑定农机、北斗设备' },
  { key: 'notify', icon: Bell, label: '通知与消息', desc: '消息管理、通知设置' },
  { key: 'team', icon: Users, label: '成员与团队', desc: '团队成员、角色权限' },
  { key: 'usage', icon: BarChart3, label: '使用与数据', desc: '用量统计、数据导出' },
  { key: 'about', icon: Info, label: '关于平台', desc: '版本、协议、联系我们' },
]

const userInfo = reactive({ id: '', role: 'farmer', created: '' })
const userProfile = reactive({ username: '', phone: '', area: '', role: 'farmer', verified: false, twoFactor: false })
const userStats = ref({ service_days: 0, field_count: 0, total_carbon_tco2e: 0, last_sync: '' })
const pwd = reactive({ old: '', new1: '', new2: '' })
const pwdMsg = ref('')

const platformSettings = reactive({ centerLon: 126.33, centerLat: 45.39, zoom: 10, geeProxy: '' })

// 表单数据
const phoneForm = reactive({ newPhone: '', code: '', error: '', success: '', loading: false })
const verifyForm = reactive({ realName: '', idCard: '', error: '', success: '', loading: false })
const deleteForm = reactive({ password: '', confirm: '', error: '', loading: false })
const inviteForm = reactive({ username: '', displayName: '', role: 'viewer', error: '', success: '', loading: false })
const deviceForm = reactive({ name: '', deviceType: 'drone', model: '', serialNumber: '', error: '', success: '', loading: false })

const securityLevel = computed(() => {
  let score = 40
  if (userProfile.phone) score += 15
  if (userProfile.verified) score += 20
  if (userProfile.twoFactor) score += 25
  if (score >= 80) return { text: '优秀', class: 'good', percent: score, tip: '您的账户安全性很好' }
  if (score >= 60) return { text: '良好', class: 'good', percent: score, tip: '建议开启双重验证以提升安全性' }
  return { text: '一般', class: 'warn', percent: score, tip: '建议完善安全设置' }
})

// 真实设备数据（从API加载）
const apiDevices = ref([])

const loginDevices = ref([])

const notifySettings = ref([])
const notifications = ref([])

const teamMembers = ref([])

// ─── 工具函数 ───
function stringToColor(str) {
  const colors = ['#16a34a', '#3b82f6', '#d97706', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

function roleLabel(role) {
  return { admin: '管理员', editor: '编辑者', viewer: '观察者' }[role] || role
}

function deviceIcon(type) {
  const map = { drone: Plane, sensor: Radio, gateway: Monitor, tractor: Tractor, phone: Smartphone }
  return map[type] || Truck
}

function deviceColor(type) {
  const map = {
    drone: { bg: 'rgba(59,130,246,0.08)', color: '#3B82F6' },
    sensor: { bg: 'rgba(217,119,6,0.08)', color: '#D97706' },
    gateway: { bg: 'rgba(139,92,246,0.08)', color: '#8B5CF6' },
    tractor: { bg: 'rgba(46,200,93,0.08)', color: '#22C55E' },
    phone: { bg: 'rgba(236,72,153,0.08)', color: '#EC4899' },
  }
  return map[type] || { bg: '#f5f5f5', color: '#888' }
}

function resetForm(form) {
  Object.keys(form).forEach(k => {
    if (k === 'loading') form[k] = false
    else if (k === 'role') form[k] = 'viewer'
    else form[k] = ''
  })
}

// ─── 初始化加载 ───
onMounted(async () => {
  try {
    const { data } = await api.get('/auth/me')
    if (data) {
      userProfile.username = data.username
      userProfile.phone = data.phone || ''
      userProfile.area = data.area || ''
      userProfile.role = data.role || 'farmer'
      userProfile.verified = data.verified || false
      userProfile.twoFactor = data.two_factor_enabled || false
      userInfo.id = data.username || data.id
      userInfo.role = data.role || 'farmer'
      if (data.created_at) userInfo.created = data.created_at
    }
  } catch {
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]))
        userInfo.id = (payload.sub || '').slice(0, 16)
        userInfo.role = payload.role || 'farmer'
      }
    } catch {}
  }
  try {
    const { data } = await api.get('/auth/stats')
    if (data) userStats.value = data
  } catch {}

  // 加载通知设置
  loadNotifySettings()
  // 加载团队成员
  loadTeamMembers()
  // 加载设备列表
  loadDevices()
  // 加载登录设备
  loadLoginDevices()
  // 加载通知消息
  loadMessages()

  const saved = localStorage.getItem('agrispatial_settings')
  if (saved) Object.assign(platformSettings, JSON.parse(saved))
})

async function loadNotifySettings() {
  try {
    const { data } = await api.get('/settings/notifications')
    if (data) notifySettings.value = data
  } catch {
    // 回退到默认值
    notifySettings.value = [
      { type: 'system', label: '系统通知', enabled: true },
      { type: 'weather', label: '气象预警', enabled: true },
      { type: 'field', label: '田块动态', enabled: true },
      { type: 'carbon', label: '碳汇报告', enabled: false },
      { type: 'alarm', label: '设备告警', enabled: true },
    ]
  }
}

async function loadTeamMembers() {
  try {
    const { data } = await api.get('/settings/team')
    if (data) teamMembers.value = data
  } catch {}
}

async function loadDevices() {
  try {
    const { data } = await api.get('/settings/devices')
    if (data) apiDevices.value = data
  } catch {}
}

// ─── 修改手机号 ───
function openPhoneModal() {
  resetForm(phoneForm)
  showPhoneModal.value = true
}

async function sendCode() {
  if (!phoneForm.newPhone) { phoneForm.error = '请先输入新手机号'; return }
  try {
    await api.post('/settings/send-code', { phone: phoneForm.newPhone })
    phoneForm.error = ''
    codeCooldown.value = 60
    const timer = setInterval(() => {
      codeCooldown.value--
      if (codeCooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (err) {
    phoneForm.error = err.response?.data?.detail || '发送失败'
  }
}

async function submitPhone() {
  phoneForm.error = ''; phoneForm.success = ''; phoneForm.loading = true
  try {
    await api.put('/settings/phone', { new_phone: phoneForm.newPhone, code: phoneForm.code })
    userProfile.phone = phoneForm.newPhone
    phoneForm.success = '手机号修改成功'
    setTimeout(() => { showPhoneModal.value = false }, 1500)
  } catch (err) {
    phoneForm.error = err.response?.data?.detail || '修改失败'
  } finally {
    phoneForm.loading = false
  }
}

// ─── 实名认证 ───
function openVerifyModal() {
  if (userProfile.verified) return
  resetForm(verifyForm)
  showVerifyModal.value = true
}

async function submitVerify() {
  verifyForm.error = ''; verifyForm.success = ''; verifyForm.loading = true
  try {
    await api.post('/settings/verify-identity', { real_name: verifyForm.realName, id_card: verifyForm.idCard })
    userProfile.verified = true
    verifyForm.success = '实名认证成功！'
    setTimeout(() => { showVerifyModal.value = false }, 1500)
  } catch (err) {
    verifyForm.error = err.response?.data?.detail || '认证失败'
  } finally {
    verifyForm.loading = false
  }
}

// ─── 注销账号 ───
async function submitDelete() {
  deleteForm.error = ''; deleteForm.loading = true
  try {
    await api.post('/settings/delete-account', { password: deleteForm.password, confirm: deleteForm.confirm })
    localStorage.removeItem('token')
    router.push('/login')
  } catch (err) {
    deleteForm.error = err.response?.data?.detail || '注销失败'
    deleteForm.loading = false
  }
}

// ─── 邀请成员 ───
async function submitInvite() {
  inviteForm.error = ''; inviteForm.success = ''; inviteForm.loading = true
  try {
    await api.post('/settings/team', {
      username: inviteForm.username,
      display_name: inviteForm.displayName || null,
      role: inviteForm.role,
    })
    inviteForm.success = '邀请已发送'
    loadTeamMembers()
    setTimeout(() => { showInviteModal.value = false }, 1500)
  } catch (err) {
    inviteForm.error = err.response?.data?.detail || '邀请失败'
  } finally {
    inviteForm.loading = false
  }
}

async function removeMember(id) {
  try {
    await api.delete(`/settings/team/${id}`)
    loadTeamMembers()
  } catch {}
}

// ─── 绑定设备 ───
async function submitDevice() {
  deviceForm.error = ''; deviceForm.success = ''; deviceForm.loading = true
  try {
    await api.post('/settings/devices', {
      name: deviceForm.name,
      device_type: deviceForm.deviceType,
      model: deviceForm.model || null,
      serial_number: deviceForm.serialNumber || null,
    })
    deviceForm.success = '设备绑定成功'
    loadDevices()
    setTimeout(() => { showAddDeviceModal.value = false }, 1500)
  } catch (err) {
    deviceForm.error = err.response?.data?.detail || '绑定失败'
  } finally {
    deviceForm.loading = false
  }
}

// ─── 通知设置 ───
async function saveNotifySetting(n) {
  try {
    await api.put(`/settings/notifications/${n.type}`, { enabled: n.enabled })
  } catch {}
}

// ─── 两步验证 ───
async function toggle2FA() {
  const newVal = !userProfile.twoFactor
  try {
    await api.put('/settings/2fa', { enabled: newVal })
    userProfile.twoFactor = newVal
  } catch {}
}

// ─── 通知消息 ───
async function loadMessages() {
  try {
    const { data } = await api.get('/settings/messages')
    if (data) notifications.value = data
  } catch {}
}

async function markRead(id) {
  try {
    await api.put(`/settings/messages/${id}/read`)
    const n = notifications.value.find(n => n.id === id)
    if (n) n.read = true
  } catch {}
}

// ─── 登录设备管理 ───
async function loadLoginDevices() {
  try {
    const { data } = await api.get('/settings/login-devices')
    if (data) loginDevices.value = data
  } catch {}
}

function formatDeviceTime(isoStr) {
  if (!isoStr) return '未知'
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 30) return `${diffDay} 天前`
  return d.toLocaleDateString('zh-CN')
}

async function revokeDevice(id) {
  try {
    await api.delete(`/settings/login-devices/${id}`)
    loginDevices.value = loginDevices.value.filter(d => d.id !== id)
  } catch {}
}

// ─── 密码修改 ───
async function changePassword() {
  if (pwd.new1 !== pwd.new2) { pwdMsg.value = '两次密码不一致'; return }
  if (pwd.new1.length < 6) { pwdMsg.value = '密码至少6位'; return }
  try {
    await api.post('/auth/change-password', { old_password: pwd.old, new_password: pwd.new1 })
    pwdMsg.value = '密码修改成功'
    pwd.old = ''; pwd.new1 = ''; pwd.new2 = ''
  } catch (err) {
    pwdMsg.value = err.response?.data?.detail || '修改失败'
  }
}

// ─── 平台设置 ───
function savePlatformSettings() {
  localStorage.setItem('agrispatial_settings', JSON.stringify({ ...platformSettings }))
  platformMsg.value = '设置已保存，下次进入地图生效'
  setTimeout(() => { platformMsg.value = '' }, 2000)
}

async function testGEE() {
  testingGEE.value = true; geeTestResult.value = ''
  try {
    const { data } = await api.get('/raster/list')
    const layers = Object.keys(data || {}).length
    geeStatus.value = '已连接'
    geeTestResult.value = `✓ 正常 — ${layers}个栅格图层可用`
  } catch (err) {
    geeStatus.value = '未连接'
    geeTestResult.value = '✗ 连接失败 — ' + (err.response?.data?.detail || err.message)
  } finally { testingGEE.value = false }
}

function clearCache() {
  localStorage.removeItem('agrispatial_settings')
  cacheMsg.value = '缓存已清除'
  setTimeout(() => { cacheMsg.value = '' }, 2000)
}

async function exportData(type) {
  try {
    const res = await api.get(`/settings/export/${type}`, { responseType: 'blob' })
    const ext = type === 'fields' ? 'json' : 'csv'
    const names = { fields: '田块数据', carbon: '碳汇报告', ndvi: 'NDVI时序' }
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${names[type]}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    alert('导出失败，请重试')
  }
}

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.settings-page { display: flex; min-height: 100%; background: #f5f7f5; }

.sidenav { width: 200px; flex-shrink: 0; padding: 20px 12px; display: flex; flex-direction: column; justify-content: space-between; border-right: 1px solid #e8ece8; background: #fff; }
.sidenav-list { display: flex; flex-direction: column; gap: 2px; }
.sidenav-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; border: none; background: none; cursor: pointer; color: #666; text-align: left; width: 100%; transition: all 0.15s; }
.sidenav-item:hover { background: #f0f5f0; color: #333; }
.sidenav-item.active { background: #e8f5e9; color: #16a34a; border-left: 3px solid #16a34a; padding-left: 9px; }
.sidenav-item.active .sidenav-desc { color: #16a34a; }
.sidenav-text { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.sidenav-label { font-size: 13px; font-weight: 600; }
.sidenav-desc { font-size: 11px; color: #999; }
.sidenav-arrow { color: #ccc; flex-shrink: 0; opacity: 0; transition: opacity 0.15s; }
.sidenav-item:hover .sidenav-arrow { opacity: 1; }

.sidenav-footer { margin-top: auto; }
.sync-banner { position: relative; border-radius: 10px; overflow: hidden; height: 90px; }
.sync-bg { width: 100%; height: 100%; object-fit: cover; display: block; }
.sync-overlay { position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.2) 100%); display: flex; flex-direction: column; justify-content: flex-end; padding: 10px 12px; }
.sync-row { display: flex; align-items: center; gap: 6px; color: #fff; font-size: 12px; font-weight: 600; }
.sync-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.sync-text { flex: 1; }
.sync-sub { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 2px; }

.mid-col { width: 280px; flex-shrink: 0; padding: 24px 20px; display: flex; flex-direction: column; gap: 16px; }
.profile-card { background: #fff; border-radius: 14px; padding: 28px 20px; text-align: center; border: 1px solid #e8ece8; }
.avatar-ring { width: 72px; height: 72px; margin: 0 auto 12px; border-radius: 50%; padding: 3px; background: linear-gradient(135deg, #22c55e, #16a34a); }
.avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 2px solid #fff; }
.profile-name { font-size: 17px; font-weight: 700; color: #1a1a1a; }
.role-badge { display: inline-block; margin-top: 6px; padding: 3px 12px; background: #e8f5e9; color: #16a34a; border-radius: 20px; font-size: 12px; font-weight: 500; }
.profile-stats { display: flex; justify-content: center; gap: 24px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.pstat { display: flex; flex-direction: column; align-items: center; }
.pstat-num { font-size: 20px; font-weight: 700; color: #1a1a1a; font-family: 'SF Mono', monospace; }
.pstat-label { font-size: 11px; color: #888; margin-top: 2px; }
.pstat-divider { width: 1px; background: #e8e8e8; }

.security-card { background: #fff; border-radius: 14px; padding: 20px; border: 1px solid #e8ece8; }
.sec-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.sec-icon { width: 36px; height: 36px; border-radius: 10px; background: #e8f5e9; color: #16a34a; display: flex; align-items: center; justify-content: center; }
.sec-title { font-size: 13px; font-weight: 600; color: #1a1a1a; }
.sec-level { font-size: 12px; font-weight: 600; }
.sec-level.good { color: #16a34a; }
.sec-level.warn { color: #d97706; }
.sec-bar { height: 6px; background: #e8e8e8; border-radius: 3px; overflow: hidden; margin-bottom: 8px; }
.sec-bar-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #16a34a); border-radius: 3px; transition: width 0.5s; }
.sec-tip { font-size: 12px; color: #888; margin-bottom: 4px; }
.sec-link { font-size: 12px; color: #16a34a; font-weight: 500; cursor: pointer; }
.sec-link:hover { text-decoration: underline; }

.main-col { flex: 1; min-width: 0; padding: 24px 28px; overflow-y: auto; }
.main-head { margin-bottom: 20px; }
.main-head h1 { font-size: 22px; font-weight: 700; color: #1a1a1a; margin: 0; }
.main-head p { font-size: 13px; color: #888; margin: 4px 0 0; }
.content-grid { display: grid; grid-template-columns: 1fr 300px; gap: 20px; }

.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid #e8ece8; margin-bottom: 16px; }
.card-head { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: #1a1a1a; margin-bottom: 14px; }
.card-desc { font-size: 12px; color: #888; margin-bottom: 14px; }

.info-rows { display: flex; flex-direction: column; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 11px 0; border-bottom: 1px solid #f5f5f5; }
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 13px; color: #666; }
.info-val { font-size: 13px; color: #1a1a1a; font-weight: 500; display: flex; align-items: center; gap: 8px; }
.info-val.mono { font-family: 'SF Mono', monospace; font-size: 12px; }
.btn-inline { padding: 3px 10px; border-radius: 6px; border: 1px solid #e0e0e0; background: #fff; color: #555; font-size: 12px; cursor: pointer; transition: all 0.15s; }
.btn-inline:hover { border-color: #16a34a; color: #16a34a; }
.verified { color: #16a34a; display: flex; align-items: center; gap: 4px; font-size: 13px; }
.unverified { color: #999; display: flex; align-items: center; gap: 6px; font-size: 13px; }

.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #333; margin-bottom: 6px; }
.input-wrap { position: relative; display: flex; align-items: center; }
.input-wrap input { width: 100%; padding: 10px 36px 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 13px; color: #333; background: #fff; transition: border-color 0.15s; }
.input-wrap input:focus { outline: none; border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.08); }
.eye-btn { position: absolute; right: 8px; background: none; border: none; color: #999; cursor: pointer; padding: 4px; }
.eye-btn:hover { color: #555; }
.form-input { width: 100%; padding: 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 13px; color: #333; }
.form-input:focus { outline: none; border-color: #16a34a; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.form-actions { display: flex; align-items: center; gap: 12px; }
.input-with-btn { display: flex; gap: 8px; }
.input-with-btn .form-input { flex: 1; }
.form-tip { font-size: 11px; color: #999; margin-bottom: 12px; }
.form-error { font-size: 12px; color: #ef4444; margin-bottom: 12px; }
.form-success { font-size: 12px; color: #16a34a; margin-bottom: 12px; }

.btn-green { padding: 10px 24px; border-radius: 8px; border: none; background: #16a34a; color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.btn-green:hover { background: #15803d; }
.btn-green:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 10px 24px; border-radius: 8px; border: none; background: #ef4444; color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.btn-danger:hover { background: #dc2626; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-block { width: 100%; }
.btn-outline { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; border: 1px solid #e0e0e0; background: #fff; color: #333; font-size: 13px; cursor: pointer; transition: all 0.15s; margin-right: 8px; margin-bottom: 8px; }
.btn-outline:hover { border-color: #16a34a; color: #16a34a; }
.btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
.action-msg { font-size: 12px; color: #888; margin-left: 12px; }
.action-msg.success { color: #16a34a; }
.action-msg.error { color: #ef4444; }

.security-banner { display: flex; align-items: center; gap: 16px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #bbf7d0; }
.sb-icon { width: 48px; height: 48px; border-radius: 50%; background: #16a34a; color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.sb-body h3 { font-size: 14px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.sb-body p { font-size: 12px; color: #666; margin-bottom: 6px; }
.sb-link { font-size: 12px; color: #16a34a; font-weight: 500; cursor: pointer; }

.action-list { display: flex; flex-direction: column; }
.action-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; cursor: pointer; transition: background 0.1s; }
.action-item:last-child { border-bottom: none; }
.action-item:hover { background: #fafafa; margin: 0 -8px; padding: 12px 8px; border-radius: 8px; }
.action-icon { width: 36px; height: 36px; border-radius: 10px; background: #f5f5f5; color: #555; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.action-info { flex: 1; min-width: 0; }
.action-title { font-size: 13px; font-weight: 600; color: #1a1a1a; display: block; }
.action-sub { font-size: 11px; color: #999; display: block; margin-top: 2px; }
.action-arrow { color: #ccc; flex-shrink: 0; }
.status-tag { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }
.status-tag.on { color: #16a34a; background: #e8f5e9; }
.status-tag.off { color: #999; background: #f5f5f5; }

.help-link { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #555; cursor: pointer; margin-top: 8px; }
.help-link:hover { color: #16a34a; }

.badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.badge-success { background: #e8f5e9; color: #16a34a; }
.badge-warning { background: #fef3c7; color: #d97706; }

.device-list { display: flex; flex-direction: column; gap: 8px; }
.device-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 8px; border: 1px solid #f0f0f0; }
.device-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.device-info { flex: 1; }
.device-name { font-size: 13px; font-weight: 600; color: #1a1a1a; }
.device-meta { font-size: 11px; color: #999; margin-top: 2px; }

.toggle-list { display: flex; flex-direction: column; }
.toggle-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f5f5f5; }
.toggle-item:last-child { border-bottom: none; }
.toggle-label { font-size: 13px; font-weight: 600; color: #1a1a1a; display: block; }
.toggle-desc { font-size: 11px; color: #999; display: block; margin-top: 2px; }
.switch { position: relative; width: 40px; height: 22px; flex-shrink: 0; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; inset: 0; background: #ddd; border-radius: 11px; cursor: pointer; transition: 0.2s; }
.slider::before { content: ''; position: absolute; width: 18px; height: 18px; border-radius: 50%; background: #fff; left: 2px; top: 2px; transition: 0.2s; }
.switch input:checked + .slider { background: #16a34a; }
.switch input:checked + .slider::before { transform: translateX(18px); }

.msg-list { display: flex; flex-direction: column; }
.msg-item { display: flex; align-items: flex-start; gap: 10px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; }
.msg-item:last-child { border-bottom: none; }
.msg-item.unread { background: #f9fdf9; margin: 0 -8px; padding: 12px 8px; border-radius: 8px; }
.msg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.msg-body { flex: 1; }
.msg-text { font-size: 13px; color: #333; display: block; }
.msg-time { font-size: 11px; color: #999; margin-top: 2px; display: block; }
.empty-text { font-size: 13px; color: #999; text-align: center; padding: 24px; }

.team-list { display: flex; flex-direction: column; gap: 8px; }
.team-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 8px; border: 1px solid #f0f0f0; }
.team-avatar { width: 36px; height: 36px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.team-info { flex: 1; }
.team-name { font-size: 13px; font-weight: 600; color: #1a1a1a; display: block; }
.team-role { font-size: 11px; color: #999; }
.team-status { font-size: 11px; color: #999; }
.team-status.online { color: #16a34a; }

.usage-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.usage-item { text-align: center; padding: 16px; background: #f9faf9; border-radius: 10px; }
.usage-num { font-size: 20px; font-weight: 700; color: #1a1a1a; display: block; font-family: 'SF Mono', monospace; }
.usage-label { font-size: 11px; color: #888; margin-top: 4px; display: block; }

.export-list { display: flex; flex-wrap: wrap; gap: 8px; }

.verify-notice { display: flex; align-items: flex-start; gap: 10px; padding: 12px; background: #f0fdf4; border-radius: 8px; margin-bottom: 16px; font-size: 12px; color: #16a34a; line-height: 1.5; }

.delete-warn { display: flex; gap: 12px; padding: 16px; background: #fef2f2; border-radius: 8px; margin-bottom: 16px; color: #ef4444; }
.delete-warn strong { font-size: 14px; display: block; margin-bottom: 4px; }
.delete-warn p { font-size: 12px; margin: 4px 0; }
.delete-warn ul { font-size: 12px; margin: 4px 0; padding-left: 16px; }
.delete-warn li { margin-bottom: 2px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: #fff; border-radius: 16px; width: 480px; max-height: 80vh; box-shadow: 0 20px 60px rgba(0,0,0,0.2); overflow: hidden; }
.modal-box.modal-danger { border: 1px solid #fecaca; }
.modal-head { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f0f0f0; }
.modal-head h3 { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.modal-close { background: none; border: none; color: #999; cursor: pointer; padding: 4px; }
.modal-close:hover { color: #333; }
.modal-body { padding: 20px; max-height: 60vh; overflow-y: auto; }

@media (max-width: 1100px) { .content-grid { grid-template-columns: 1fr; } }
@media (max-width: 900px) {
  .settings-page { flex-direction: column; }
  .sidenav { width: 100%; flex-direction: row; overflow-x: auto; padding: 12px; border-right: none; border-bottom: 1px solid #e8ece8; }
  .sidenav-list { flex-direction: row; gap: 4px; }
  .sidenav-footer { display: none; }
  .mid-col { width: 100%; flex-direction: row; padding: 16px; gap: 12px; }
  .usage-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
