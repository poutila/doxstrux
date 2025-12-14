# Test: 31_script_tag_multiline

Normal text

<script type="text/javascript">
  var x = "malicious";
  document.write(x);
</script>

More text.
