import frappe


def run():
	HTML = r"""<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>SBIQ - Core | License Management Portal</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config={darkMode:"class",theme:{extend:{"colors":{"outline-variant":"#c6c6cd","primary-container":"#131b2e","surface-container":"#eceef0","surface-variant":"#e0e3e5","on-tertiary-fixed-variant":"#38485d","secondary":"#006591","on-secondary":"#ffffff","surface-container-lowest":"#ffffff","on-primary":"#ffffff","on-surface-variant":"#45464d","on-surface":"#191c1e","primary":"#0f172a","surface-container-low":"#f2f4f6","outline":"#76777d","surface-container-high":"#e6e8ea","tertiary-container":"#0b1c30","on-tertiary-container":"#75859d","background":"#f7f9fb","secondary-container":"#39b8fd","on-secondary-container":"#004666","error":"#ba1a1a","on-error":"#ffffff"},"borderRadius":{"DEFAULT":"0.25rem","lg":"0.5rem","xl":"0.75rem","full":"9999px"},"spacing":{"gutter":"24px","margin-mobile":"16px","margin-desktop":"40px","container-max":"1440px","base":"8px"},"fontFamily":{"headline-md":["Inter"],"body-lg":["Inter"],"body-md":["Inter"],"label-md":["Inter"],"display-lg":["Inter"],"body-sm":["Inter"],"label-sm":["Inter"]},"fontSize":{"headline-md":["24px",{"lineHeight":"32px","fontWeight":"600"}],"body-lg":["18px",{"lineHeight":"28px","fontWeight":"400"}],"body-md":["16px",{"lineHeight":"24px","fontWeight":"400"}],"label-md":["14px",{"lineHeight":"20px","fontWeight":"500"}],"display-lg":["48px",{"lineHeight":"56px","letterSpacing":"-0.02em","fontWeight":"700"}],"body-sm":["14px",{"lineHeight":"20px","fontWeight":"400"}],"label-sm":["12px",{"lineHeight":"16px","fontWeight":"600"}]}}}}
</script>
<style>
body{background-color:#F8FAFC}
.ambient-shadow{box-shadow:0px 1px 3px rgba(15,23,42,0.08)}
#license-details{display:none}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.4);border-top-color:#fff;border-radius:50%;animation:spin 0.7s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body class="font-sans antialiased text-on-background min-h-screen flex flex-col">
<nav class="bg-surface-container-lowest text-primary border-b border-surface-variant shadow-sm sticky top-0 z-50">
<div class="flex justify-between items-center w-full px-margin-desktop max-w-container-max mx-auto h-20">
<div class="font-headline-md text-headline-md font-bold text-primary">SBIQ - Core</div>
<div class="hidden md:flex items-center gap-gutter">
<a class="text-secondary font-semibold border-b-2 border-secondary pb-1" href="#">Obtain Key</a>
<a class="text-on-surface-variant hover:text-primary transition-colors" href="#">Verify</a>
<a class="text-on-surface-variant hover:text-primary transition-colors" href="#">Issue</a>
<a class="text-on-surface-variant hover:text-primary transition-colors" href="#">Support</a>
<a class="text-on-surface-variant hover:text-primary transition-colors" href="#">Documentation</a>
</div>
</div>
</nav>
<main class="flex-grow w-full max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-12 flex flex-col gap-16">
<section class="text-center max-w-3xl mx-auto flex flex-col items-center gap-6">
<h1 class="font-display-lg text-display-lg text-primary">License Key Verification &amp; Issuance</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Enterprise-grade security powered by Hephzibah Technologies.</p>
</section>
<section class="bg-surface-container-lowest rounded-lg ambient-shadow p-8 flex flex-col gap-8 border border-surface-variant">
<div class="border-b border-surface-container pb-4">
<h2 class="font-headline-md text-headline-md text-primary flex items-center gap-2">
<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1">vpn_key</span>
Obtain License Key
</h2>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-1">Retrieve your license key securely via email verification.</p>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-12">
<div class="flex flex-col gap-8">
<div class="flex flex-col gap-4">
<div class="flex flex-col gap-2">
<label class="font-label-md text-label-md text-on-surface" for="email-input">1. Enter Email</label>
<input class="w-full px-4 py-3 bg-surface-container-lowest border border-surface-variant rounded focus:outline-none focus:border-secondary font-body-md text-body-md transition-all" id="email-input" placeholder="admin@company.com" type="email"/>
</div>
<div id="otp-msg" class="hidden text-sm font-medium"></div>
<button id="btn-generate" class="bg-primary text-on-primary font-label-md text-label-md px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95 duration-150 self-start">
Generate OTP
</button>
</div>
<div class="flex flex-col gap-4">
<div class="flex flex-col gap-2">
<label class="font-label-md text-label-md text-on-surface" for="otp-input">2. Enter OTP</label>
<input class="w-full px-4 py-3 bg-surface-container-lowest border border-surface-variant rounded focus:outline-none focus:border-secondary font-body-md text-body-md transition-all font-mono tracking-widest" id="otp-input" placeholder="123456" type="text" maxlength="6"/>
</div>
<div id="verify-msg" class="hidden text-sm font-medium"></div>
<button id="btn-verify" class="bg-secondary text-on-secondary font-label-md text-label-md px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity flex items-center gap-2 self-start">
<span class="material-symbols-outlined">verified</span>Verify and Get Key
</button>
</div>
</div>
<div id="license-details" class="bg-surface-container-low rounded-lg border border-outline-variant p-6 flex flex-col gap-6">
<h3 class="font-label-md text-label-md text-on-surface-variant flex items-center gap-2 uppercase tracking-wider">
<span class="material-symbols-outlined text-[18px]">assignment</span>License Details
</h3>
<div class="flex flex-col gap-5">
<div class="flex flex-col gap-1">
<span class="font-label-sm text-label-sm text-on-surface-variant uppercase">License Key</span>
<div class="font-mono text-primary font-bold bg-surface-container-lowest px-4 py-3 border border-surface-variant rounded flex justify-between items-center text-lg">
<span id="ld-key">—</span>
<button onclick="copyKey()" class="text-secondary hover:text-primary transition-colors"><span class="material-symbols-outlined text-[20px]">content_copy</span></button>
</div>
</div>
<div class="grid grid-cols-2 gap-4">
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Customer</span><span id="ld-customer" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Product</span><span id="ld-product" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Purchase Date</span><span id="ld-purchase" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Expiry</span><span id="ld-expiry" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Amount Paid</span><span id="ld-amount" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
<div class="flex flex-col gap-1"><span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Invoice</span><span id="ld-invoice" class="font-body-md text-body-md text-on-surface font-medium">—</span></div>
</div>
<div class="flex flex-col gap-1 mt-2">
<span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Status</span>
<span id="ld-status" class="inline-flex items-center gap-1.5 text-[#15803d] bg-[#dcfce7] px-3 py-1.5 rounded-full text-label-md font-label-md w-max border border-[#bbf7d0]">
<span class="material-symbols-outlined text-[18px]">check_circle</span>Active
</span>
</div>
</div>
</div>
</div>
</section>
</main>
<footer class="bg-surface-container text-on-surface font-label-sm text-label-sm border-t border-surface-variant mt-auto">
<div class="w-full py-12 px-margin-desktop max-w-container-max mx-auto flex flex-col md:flex-row justify-between items-center gap-base">
<div class="font-headline-md text-headline-md font-bold">SBIQ - Core</div>
<div class="flex flex-wrap justify-center gap-x-6 gap-y-2">
<a class="text-on-surface-variant hover:text-primary hover:underline transition-all" href="#">Privacy Policy</a>
<a class="text-on-surface-variant hover:text-primary hover:underline transition-all" href="#">Terms of Service</a>
<a class="text-on-surface-variant hover:text-primary hover:underline transition-all" href="#">Security Audit</a>
<a class="text-on-surface-variant hover:text-primary hover:underline transition-all" href="#">Contact Global Support</a>
</div>
<div class="text-center md:text-right text-on-surface-variant">&copy; 2024 Hephzibah Technologies. All rights reserved.</div>
</div>
</footer>
<script>
const API='/api/method/erpnext.mft_license_api';
function msg(id,text,err){const e=document.getElementById(id);e.textContent=text;e.className='text-sm font-medium '+(err?'text-red-600':'text-green-600');e.classList.remove('hidden');}
document.getElementById('btn-generate').addEventListener('click',async()=>{
const email=document.getElementById('email-input').value.trim();
const btn=document.getElementById('btn-generate');
if(!email){msg('otp-msg','Please enter your email.',true);return;}
btn.disabled=true;btn.innerHTML='<span class="spinner"></span> Sending...';
document.getElementById('otp-msg').classList.add('hidden');
try{
const r=await fetch(API+'.generate_otp',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':'fetch'},body:JSON.stringify({email})});
const d=await r.json();
if(!r.ok)throw new Error((d.exception||'').split('\n').pop()||d.message||'Failed');
msg('otp-msg','OTP sent to your email. Valid for 10 minutes.',false);
}catch(e){msg('otp-msg',e.message,true);}
finally{btn.disabled=false;btn.textContent='Generate OTP';}
});
document.getElementById('btn-verify').addEventListener('click',async()=>{
const email=document.getElementById('email-input').value.trim();
const otp=document.getElementById('otp-input').value.trim();
const btn=document.getElementById('btn-verify');
if(!email||!otp){msg('verify-msg','Enter both email and OTP.',true);return;}
btn.disabled=true;btn.innerHTML='<span class="material-symbols-outlined">verified</span><span class="spinner"></span>';
document.getElementById('verify-msg').classList.add('hidden');
try{
const r=await fetch(API+'.verify_otp',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':'fetch'},body:JSON.stringify({email,otp})});
const d=await r.json();
if(!r.ok)throw new Error((d.exception||'').split('\n').pop()||d.message||'Verification failed');
const l=d.message;
document.getElementById('ld-key').textContent=l.license_key;
document.getElementById('ld-customer').textContent=l.customer;
document.getElementById('ld-product').textContent=l.product;
document.getElementById('ld-purchase').textContent=l.purchase_date||'—';
document.getElementById('ld-expiry').textContent=l.expiry||'Lifetime';
document.getElementById('ld-amount').textContent=l.amount_paid?'&#8377;'+l.amount_paid:'—';
document.getElementById('ld-invoice').textContent=l.invoice_number||'—';
document.getElementById('ld-status').innerHTML='<span class="material-symbols-outlined text-[18px]">check_circle</span> '+l.status;
document.getElementById('license-details').style.display='flex';
msg('verify-msg','Verified successfully!',false);
}catch(e){msg('verify-msg',e.message,true);}
finally{btn.disabled=false;btn.innerHTML='<span class="material-symbols-outlined">verified</span> Verify and Get Key';}
});
function copyKey(){navigator.clipboard.writeText(document.getElementById('ld-key').textContent);}
</script>
</body></html>"""

	frappe.db.set_value("Web Page", "lijish-wol", "main_section_html", HTML)
	frappe.db.commit()
	print("Web page updated successfully.")
