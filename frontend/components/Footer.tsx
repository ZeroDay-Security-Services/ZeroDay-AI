import Image from 'next/image';
import logo from '@/public/logo.png';

export default function Footer() {
  return (
    <footer id="about" className="mt-10 border-t border-border px-8 pb-10 pt-[70px]">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-end justify-between gap-7">
        <div className="flex items-center gap-3.5">
          <Image src={logo} alt="ZeroDay Security Services logo" height={40} width={40} className="object-contain" />
          <div>
            <div className="font-display text-base font-bold text-text">ZeroDay Security Services</div>
            <div className="mt-0.5 font-mono text-[10.5px] tracking-widest text-steel">
              AI CYBERSECURITY INTELLIGENCE
            </div>
          </div>
        </div>

        <div className="text-left font-mono text-[11.5px] leading-loose text-steelDim md:text-right">
          Designed &amp; Developed by
          <br />
          <b className="text-steel">Vijay Ishan Chowdhury</b>
        </div>
      </div>

      <div className="mx-auto mt-10 max-w-[1200px] border-t border-border pt-5 text-center font-mono text-[10.5px] text-steelDim">
        © 2026 ZERODAY SECURITY SERVICES — ALL SYSTEMS NOMINAL
      </div>
    </footer>
  );
}
