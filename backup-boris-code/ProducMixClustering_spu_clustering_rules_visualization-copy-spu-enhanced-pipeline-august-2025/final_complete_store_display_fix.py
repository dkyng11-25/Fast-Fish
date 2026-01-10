#!/usr/bin/env python3
"""
Final Complete Store Display Fix

This script replaces all truncated store lists with complete lists
showing every single store. No more "... and X more" - the user wants
to see ALL stores.
"""

def main():
    """Update the presentation to show complete store lists."""
    print("🔄 Creating final fix to show ALL stores...")
    
    # Read the current presentation
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f'AI_Store_Planning_Executive_Presentation_backup_complete_stores_{timestamp}.html'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created backup: {backup_filename}")
    
    # Replace the insufficient data stores section (139 stores) with complete list
    insufficient_data_old = '''                        <div class="store-section">
                            <strong>Sample Store IDs:</strong><br>
                            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; max-height: 300px; overflow-y: auto; padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51114</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">52062</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">52083</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53030</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53070</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53105</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">12028</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32535</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">35032</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37077</span>
                                <span style="color: #6c757d; font-style: italic; text-align: center; grid-column: 1 / -1;">... and 129 more stores (showing first 10)</span>
                            </div>
                        </div>'''
    
    insufficient_data_new = '''                        <div class="store-section">
                            <strong>ALL Store IDs (Complete List - 139 stores):</strong><br>
                            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; max-height: 400px; overflow-y: auto; padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">12028</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31067</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31139</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31141</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31156</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31163</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31218</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31242</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31243</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31245</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">31250</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32160</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32195</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32270</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32278</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32279</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32375</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32402</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32459</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32535</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32550</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32644</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">32660</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33174</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33301</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33326</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33329</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33348</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33373</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33393</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33453</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33595</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33714</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">33736</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34024</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34049</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34077</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34088</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34098</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34109</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34110</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34149</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34151</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34173</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34201</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34234</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34283</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34297</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34322</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">34336</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">35025</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">35032</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">35112</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">35135</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">36009</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">36107</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">36149</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37077</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37097</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37108</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37117</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37126</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37143</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37146</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37151</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37154</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37174</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37176</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37210</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">37213</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41003</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41030</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41045</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41140</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41141</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41191</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41193</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41213</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41236</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">41241</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">42019</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">42057</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">42074</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">42096</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">42157</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43017</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43032</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43034</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43066</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43074</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43119</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">43167</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44106</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44109</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44123</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44124</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44153</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44163</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44188</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44208</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44299</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44307</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44325</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44336</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44362</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44368</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44419</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44479</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">44531</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45013</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45024</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45031</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45039</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45041</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45045</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45055</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45098</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">45126</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">46005</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">50031</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">50036</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">50048</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51024</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51075</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51077</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51087</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51109</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51114</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51159</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51161</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51167</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">51198</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">52062</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">52083</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">52112</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53030</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53070</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53095</span>
                                <span style="background: #6c757d; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">53105</span>
                                <span style="color: #28a745; font-weight: bold; text-align: center; grid-column: 1 / -1; background: #f8f9fa; padding: 8px; border-radius: 4px; border: 2px solid #28a745;">✅ Complete List - All 139 Stores Shown</span>
                            </div>
                        </div>'''
    
    # Apply the replacement
    if insufficient_data_old in content:
        content = content.replace(insufficient_data_old, insufficient_data_new)
        print("✅ Updated insufficient data stores to show ALL 139 stores")
    else:
        print("⚠️  Could not find insufficient data section to update")
    
    # Save the updated content
    with open('AI_Store_Planning_Executive_Presentation.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 Final fix complete! Now showing ALL stores in every category.")
    print("💡 No more truncated lists - every single store is visible!")

if __name__ == "__main__":
    main() 